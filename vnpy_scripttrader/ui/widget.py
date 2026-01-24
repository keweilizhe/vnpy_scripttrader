from pathlib import Path

from vnpy.event import EventEngine, Event
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import QtWidgets, QtCore
from vnpy.trader.object import LogData
from ..engine import APP_NAME, EVENT_SCRIPT_LOG, BaseEngine


# 默认脚本相对路径（相对于 vnpy 包的位置）
DEFAULT_SCRIPT_RELATIVE_PATH = "my_script_strategy/ming_xing_trade.py"


class ScriptManager(QtWidgets.QWidget):
    """"""
    signal_log: QtCore.Signal = QtCore.Signal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine) -> None:
        """"""
        super().__init__()

        self.main_engine: MainEngine = main_engine
        self.event_engine: EventEngine = event_engine

        self.script_engine: BaseEngine = main_engine.get_engine(APP_NAME)

        self.script_path: str = ""

        self.init_ui()
        self.register_event()
        self.load_default_script()  # 加载默认脚本路径

        self.script_engine.init()

    def init_ui(self) -> None:
        """"""
        self.setWindowTitle("脚本策略")

        start_button: QtWidgets.QPushButton = QtWidgets.QPushButton("启动")
        start_button.clicked.connect(self.start_script)

        stop_button: QtWidgets.QPushButton = QtWidgets.QPushButton("停止")
        stop_button.clicked.connect(self.stop_script)

        select_button: QtWidgets.QPushButton = QtWidgets.QPushButton("打开")
        select_button.clicked.connect(self.select_script)

        self.strategy_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()

        self.log_monitor: QtWidgets.QTextEdit = QtWidgets.QTextEdit()
        self.log_monitor.setReadOnly(True)

        clear_button: QtWidgets.QPushButton = QtWidgets.QPushButton("清空")
        clear_button.clicked.connect(self.log_monitor.clear)

        hbox: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.strategy_line)
        hbox.addWidget(select_button)
        hbox.addWidget(start_button)
        hbox.addWidget(stop_button)
        hbox.addStretch()
        hbox.addWidget(clear_button)

        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addWidget(self.log_monitor)

        self.setLayout(vbox)

    def register_event(self) -> None:
        """"""
        self.signal_log.connect(self.process_log_event)

        self.event_engine.register(EVENT_SCRIPT_LOG, self.signal_log.emit)

    def load_default_script(self) -> None:
        """
        加载默认脚本路径

        尝试多种方式定位脚本文件：
        1. 相对于 vnpy 包的位置
        2. 相对于当前工作目录
        3. 相对于项目根目录
        """
        default_path = self._find_default_script()

        if default_path and default_path.exists():
            self.script_path = str(default_path)
            self.strategy_line.setText(self.script_path)
        else:
            # 如果找不到默认脚本，显示提示
            self.strategy_line.setPlaceholderText("请选择策略脚本文件...")

    def _find_default_script(self) -> Path | None:
        """
        查找默认脚本文件

        按优先级尝试多种路径：
        1. vnpy 包同级目录
        2. 当前工作目录
        3. 环境变量 VNPY_PROJECT_ROOT

        Returns:
            找到的脚本路径，未找到返回 None
        """
        import os

        # 方法1：相对于 vnpy 包的位置
        try:
            import vnpy
            vnpy_package_dir = Path(vnpy.__file__).parent
            script_path = vnpy_package_dir / DEFAULT_SCRIPT_RELATIVE_PATH
            if script_path.exists():
                return script_path.resolve()
        except (ImportError, AttributeError):
            pass

        # 方法2：相对于当前工作目录
        cwd_path = Path.cwd() / "vnpy" / DEFAULT_SCRIPT_RELATIVE_PATH
        if cwd_path.exists():
            return cwd_path.resolve()

        # 方法3：直接在当前目录查找
        direct_path = Path.cwd() / DEFAULT_SCRIPT_RELATIVE_PATH
        if direct_path.exists():
            return direct_path.resolve()

        # 方法4：通过环境变量指定的项目根目录
        project_root = os.environ.get("VNPY_PROJECT_ROOT")
        if project_root:
            env_path = Path(project_root) / "vnpy" / DEFAULT_SCRIPT_RELATIVE_PATH
            if env_path.exists():
                return env_path.resolve()

        # 方法5：向上查找包含 vnpy 目录的父目录
        search_path = Path.cwd()
        for _ in range(5):  # 最多向上查找5层
            vnpy_dir = search_path / "vnpy"
            if vnpy_dir.is_dir():
                script_path = vnpy_dir / DEFAULT_SCRIPT_RELATIVE_PATH
                if script_path.exists():
                    return script_path.resolve()
            search_path = search_path.parent

        return None

    def show(self) -> None:
        """"""
        self.showMaximized()

    def process_log_event(self, event: Event) -> None:
        """"""
        log: LogData = event.data
        msg: str = f"{log.time}\t{log.msg}"
        self.log_monitor.append(msg)

    def start_script(self) -> None:
        """"""
        if self.script_path:
            self.script_engine.start_strategy(self.script_path)

    def stop_script(self) -> None:
        """"""
        self.script_engine.stop_strategy()

    def select_script(self) -> None:
        """
        选择脚本文件

        默认打开 vnpy/my_script_strategy 目录
        """
        # 优先使用脚本所在目录，否则使用当前工作目录
        if self.script_path:
            default_dir = str(Path(self.script_path).parent)
        else:
            default_dir = self._get_default_script_dir()

        path, type_ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "载入策略脚本",
            default_dir,
            "Python File(*.py)"
        )

        if path:
            self.script_path = path
            self.strategy_line.setText(path)

    def _get_default_script_dir(self) -> str:
        """
        获取默认的脚本目录

        Returns:
            脚本目录路径字符串
        """
        try:
            import vnpy
            vnpy_dir = Path(vnpy.__file__).parent
            script_dir = vnpy_dir / "my_script_strategy"
            if script_dir.exists():
                return str(script_dir)
        except (ImportError, AttributeError):
            pass

        return str(Path.cwd())
