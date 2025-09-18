import sys
from PyQt5.QtCore import QObject, pyqtSignal

from tools.content_export.content_export import ContentExportPlugin
# Custom stream to redirect stdout/stderr to QTextEdit
class QTextEditStream(QObject):
    write_signal = pyqtSignal(str)

    def __init__(self, text_edit):
        super().__init__()
        self.text_edit = text_edit
        self.write_signal.connect(self._append_text)

    def write(self, text):
        self.write_signal.emit(str(text))

    def flush(self):
        pass  # Required for file-like interface

    def _append_text(self, text):
        self.text_edit.moveCursor(self.text_edit.textCursor().End)
        self.text_edit.insertPlainText(text)
        self.text_edit.ensureCursorVisible()
import sys
import asyncio
import uuid
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QTextBrowser, QPushButton, QLabel
)
from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot
import markdown

import os
from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import AzureChatPromptExecutionSettings
from agents.plugin.PatientStatus import PatientStatus
from agents.plugin.PatientTimeline import PatientTimeline
from agents.plugin.TumorBoardReview import TumorBoardReview
from agents.plugin.StorageQuery import StorageQuery
from data_models.chat_context import ChatContext
from data_models.data_access import create_data_access
from dotenv import load_dotenv


class BackendWorker(QObject):
    finished = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.kernel = None
        self.chat_completion = None
        self.chat_ctx = None
        self.data_access = None
        self.history = ChatHistory()
        self.execution_settings = AzureChatPromptExecutionSettings()
        self.execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        try:
            self._init_kernel()
        except Exception as e:
            self.error_occurred.emit(f"Failed to initialize kernel: {str(e)}")

    def _init_kernel(self):
        load_dotenv()
        
        # Initialize the kernel
        self.kernel = Kernel()

        # Add Azure OpenAI chat completion
        self.chat_completion = AzureChatCompletion(
            service_id="chat_completion",
            deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
            api_key=os.getenv("AZURE_DEPLOYMENT_KEY"),
            base_url=os.getenv("AZURE_DEPLOYMENT_ENDPOINT"),
        )
        self.kernel.add_service(self.chat_completion)

        # Create a chat context with a conversation ID
        conversation_id = str(uuid.uuid4())
        self.chat_ctx = ChatContext(conversation_id=conversation_id)
        
        # Create blob service client and credential for data access
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=os.getenv("STORAGE_ACCOUNT_URL"),
            credential=credential
        )
        
        # Create data access using the factory function
        self.data_access = create_data_access(blob_service_client, credential)
        
        # Create storage plugin
        storage_plugin = StorageQuery(
            account_url=os.getenv("STORAGE_ACCOUNT_URL"),
            container_name="patient-data",
        )
        
        # Add plugins
        self.kernel.add_plugin(
            storage_plugin,
            plugin_name="PatientDataStorage",
        )
        # self.kernel.add_plugin(
        #     TumorBoardReview(
        #         kernel=self.kernel,
        #     ),
        #     plugin_name="TumorBoardReview",
        # )
        self.kernel.add_plugin(
            PatientTimeline(
                kernel=self.kernel,
            ),
            plugin_name="PatientTimeline",
        )
        self.kernel.add_plugin(
            PatientStatus(
                kernel=self.kernel,
            ),
            plugin_name="PatientStatus",
        )

        self.kernel.add_plugin(
            ContentExportPlugin(
                kernel=self.kernel, 
                chat_ctx=self.chat_ctx, 
                data_access=self.data_access),
            plugin_name="ContentExport",
        )

    @pyqtSlot()
    def clear_history(self):
        """Clear the conversation history"""
        # Remove all messages from the history
        while len(self.history.messages) > 0:
            self.history.remove_message(0)

    @pyqtSlot(str)
    def process(self, user_input):
        try:
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async function
            loop.run_until_complete(self._process_async(user_input))
            
            # Clean up the loop
            loop.close()
        except Exception as e:
            self.error_occurred.emit(f"Error processing message: {str(e)}")

    async def _process_async(self, user_input):
        try:
            self.history.add_user_message(user_input)
            result = await self.chat_completion.get_chat_message_content(
                chat_history=self.history,
                settings=self.execution_settings,
                kernel=self.kernel,
            )
            self.history.add_message(result)
            self.finished.emit(user_input, str(result))
        except Exception as e:
            self.error_occurred.emit(f"Error in async processing: {str(e)}")

class ChatUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Healthcare Orchestrator Chat')
        self.setGeometry(100, 100, 1200, 800)  # Set initial size

        # Main horizontal layout
        main_layout = QHBoxLayout()

        # Left: Chat area (vertical)
        chat_layout = QVBoxLayout()
        self.response_output = QTextBrowser()
        self.response_output.setOpenExternalLinks(True)
        self.response_output.setReadOnly(True)
        chat_layout.addWidget(QLabel('Chat History:'))
        chat_layout.addWidget(self.response_output, stretch=1)

        # Input area (horizontal at bottom)
        input_layout = QHBoxLayout()
        self.text_input = QTextEdit()
        self.text_input.setFixedHeight(60)
        self.send_button = QPushButton('Send')
        input_layout.addWidget(self.text_input, stretch=1)
        input_layout.addWidget(self.send_button)
        chat_layout.addLayout(input_layout)

        # Right: CLI log area
        log_layout = QVBoxLayout()
        log_layout.addWidget(QLabel('CLI Logs:'))
        self.cli_log_output = QTextEdit()
        self.cli_log_output.setReadOnly(True)
        self.cli_log_output.setStyleSheet('background-color: #222; color: #eee; font-family: monospace;')
        log_layout.addWidget(self.cli_log_output, stretch=1)

        # Add chat and log to main layout
        main_layout.addLayout(chat_layout, stretch=3)
        main_layout.addLayout(log_layout, stretch=2)
        self.setLayout(main_layout)

        self.send_button.clicked.connect(self.send_message)

        # Redirect stdout and stderr to CLI log panel
        sys.stdout = QTextEditStream(self.cli_log_output)
        sys.stderr = QTextEditStream(self.cli_log_output)

        # Initialize backend worker in a separate thread
        self.worker = BackendWorker()
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.display_response)
        self.worker.error_occurred.connect(self.display_error)
        self.thread.start()
        
        # Log successful initialization
        print("Healthcare Orchestrator Chat initialized successfully!")
        print("Enter your message and click Send to start chatting.")

    def send_message(self):
        user_input = self.text_input.toPlainText().strip()
        if not user_input:
            return
            
        self.text_input.clear()
        self.send_button.setEnabled(False)  # Disable while processing
        
        # Clear conversation history for each new message
        from PyQt5.QtCore import QMetaObject, Q_ARG
        QMetaObject.invokeMethod(self.worker, "clear_history")
        
        # Use QMetaObject.invokeMethod to safely call across threads
        QMetaObject.invokeMethod(self.worker, "process", Q_ARG(str, user_input))

    def display_response(self, user_input, response):
        self.response_output.append(f'<b>User:</b> {user_input}')
        html = markdown.markdown(response)
        self.response_output.append(f'<b>Assistant:</b><br>{html}')
        self.send_button.setEnabled(True)  # Re-enable send button

    def display_error(self, error_message):
        self.response_output.append(f'<b style="color: red;">Error:</b> {error_message}')
        self.send_button.setEnabled(True)  # Re-enable send button
        print(f"Error: {error_message}")

    def log_cli(self, text):
        self.cli_log_output.append(text)

    def closeEvent(self, event):
        # Clean shutdown
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        event.accept()

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Healthcare Orchestrator Chat")
        
        window = ChatUI()
        window.show()
        
        print("Application started successfully!")
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
