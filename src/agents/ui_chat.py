import sys
from PyQt5.QtCore import QObject, pyqtSignal
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
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QTextBrowser, QPushButton, QLabel
)
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import markdown

import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import AzureChatPromptExecutionSettings
from agents.plugin.PatientStatus import PatientStatus
from agents.plugin.PatientTimeline import PatientTimeline
from agents.plugin.TumorBoardReview import TumorBoardReview
from agents.plugin.StorageQuery import StorageQuery
from dotenv import load_dotenv


class BackendWorker(QObject):
    finished = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.kernel = None
        self.chat_completion = None
        self.history = ChatHistory()
        self.execution_settings = AzureChatPromptExecutionSettings()
        self.execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        self._init_kernel()

    def _init_kernel(self):
        load_dotenv()
        self.kernel = Kernel()
        self.chat_completion = AzureChatCompletion(
            service_id="chat_completion",
            deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
            api_key=os.getenv("AZURE_DEPLOYMENT_KEY"),
            base_url=os.getenv("AZURE_DEPLOYMENT_ENDPOINT"),
        )
        self.kernel.add_service(self.chat_completion)
        self.kernel.add_plugin(StorageQuery(
            account_url=os.getenv("STORAGE_ACCOUNT_URL"),
            container_name="patient-data",
        ), plugin_name="PatientDataStorage")
        self.kernel.add_plugin(TumorBoardReview(self.kernel), plugin_name="TumorBoardReview")
        self.kernel.add_plugin(PatientTimeline(self.kernel), plugin_name="PatientTimeline")
        self.kernel.add_plugin(PatientStatus(self.kernel), plugin_name="PatientStatus")

    def process(self, user_input):
        asyncio.run(self._process_async(user_input))

    async def _process_async(self, user_input):
        self.history.add_user_message(user_input)
        result = await self.chat_completion.get_chat_message_content(
            chat_history=self.history,
            settings=self.execution_settings,
            kernel=self.kernel,
        )
        self.history.add_message(result)
        self.finished.emit(user_input, str(result))

class ChatUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Healthcare Orchestrator Chat')

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

        self.worker = BackendWorker()
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.display_response)
        self.thread.start()

    def send_message(self):
        user_input = self.text_input.toPlainText()
        self.text_input.clear()
        asyncio.get_event_loop().run_in_executor(None, self.worker.process, user_input)

    def display_response(self, user_input, response):
        self.response_output.append(f'<b>User:</b> {user_input}')
        html = markdown.markdown(response)
        self.response_output.append(f'<b>Assistant:</b><br>{html}')

    def log_cli(self, text):
        self.cli_log_output.append(text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ChatUI()
    window.show()
    sys.exit(app.exec_())
