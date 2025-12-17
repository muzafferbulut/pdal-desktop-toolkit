from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, 
                             QTreeWidgetItem, QWidget, QTableView, QLineEdit,
                             QPushButton, QLabel, QFormLayout, QDialogButtonBox, 
                             QMessageBox, QHeaderView, QStyle, QToolBar, QAction, QFileDialog, QInputDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from core.database.inspector import DbInspector
from core.database.repository import Repository
from core.database.workers import DbQueryWorker 

class NewConnectionDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New PostGIS Connection")
        self.resize(300, 250)
        self.conn_data = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        form = QFormLayout()
        
        self.le_name = QLineEdit("Local DB")
        self.le_host = QLineEdit("localhost")
        self.le_port = QLineEdit("5432")
        self.le_db = QLineEdit()
        self.le_user = QLineEdit("postgres")
        self.le_pass = QLineEdit()
        self.le_pass.setEchoMode(QLineEdit.Password)

        form.addRow("Name:", self.le_name)
        form.addRow("Host:", self.le_host)
        form.addRow("Port:", self.le_port)
        form.addRow("Database:", self.le_db)
        form.addRow("Username:", self.le_user)
        form.addRow("Password:", self.le_pass)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._on_save)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _on_save(self):
        if not self.le_name.text() or not self.le_db.text():
            QMessageBox.warning(self, "Error", "Name and Database fields are required.")
            return
        
        self.conn_data = {
            "name": self.le_name.text(),
            "host": self.le_host.text(),
            "port": self.le_port.text(),
            "database_name": self.le_db.text(),
            "username": self.le_user.text(),
            "password": self.le_pass.text(),
            "db_type": "postgresql"
        }
        self.accept()

class DbManagerDialog(QDialog):

    def __init__(self, data_controller, parent=None):
        super().__init__(parent)
        self.data_controller = data_controller
        self.setWindowTitle("Database Manager")
        self.resize(1000, 600)
        
        self.repository = Repository()
        self.active_inspector = None
        self.current_schema = None
        self.current_table = None
        
        self._setup_ui()
        self._load_connections()

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        act_new = QAction(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), "New Connection", self)
        act_new.triggered.connect(self._open_new_conn_dialog)
        toolbar.addAction(act_new)

        act_refresh = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), "Refresh", self)
        act_refresh.triggered.connect(self._load_connections)
        toolbar.addAction(act_refresh)
        
        toolbar.addSeparator()

        act_imp_file = QAction(self.style().standardIcon(QStyle.SP_ArrowUp), "Import File to DB", self)
        act_imp_file.triggered.connect(self._action_import_file)
        toolbar.addAction(act_imp_file)

        main_layout.addWidget(toolbar)
        splitter = QSplitter(Qt.Horizontal)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Browser")
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemClicked.connect(self._on_item_clicked)
        splitter.addWidget(self.tree)

        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        filter_layout = QHBoxLayout()
        
        self.lbl_table = QLabel("No Table Selected")
        self.lbl_table.setStyleSheet("font-weight: bold; color: #555;")
        
        self.le_filter = QLineEdit()
        self.le_filter.setPlaceholderText("Filter (e.g. filename like 'file%'")
        self.le_filter.returnPressed.connect(self._run_filter_query)
        
        btn_run = QPushButton("Filter")
        btn_run.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        btn_run.clicked.connect(self._run_filter_query)

        self.btn_load_canvas = QPushButton("Load to Canvas")
        self.btn_load_canvas.setIcon(self.style().standardIcon(QStyle.SP_ArrowLeft))
        self.btn_load_canvas.clicked.connect(self._on_load_to_canvas)
        self.btn_load_canvas.setEnabled(False)

        filter_layout.addWidget(QLabel("WHERE:"))
        filter_layout.addWidget(self.le_filter)
        filter_layout.addWidget(btn_run)
        filter_layout.addStretch()
        filter_layout.addWidget(self.btn_load_canvas)
        
        top_container = QVBoxLayout()
        top_container.addWidget(self.lbl_table)
        top_container.addLayout(filter_layout)
        
        right_layout.addLayout(top_container)
        
        self.result_view = QTableView()
        right_layout.addWidget(self.result_view)
        
        right_panel.setLayout(right_layout)
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(1, 3) 
        main_layout.addWidget(splitter)

    def _load_connections(self):
        self.tree.clear()
        conns = self.repository.get_connections()
        for c in conns:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, c["name"])
            item.setIcon(0, self.style().standardIcon(QStyle.SP_DriveNetIcon))
            item.setData(0, Qt.UserRole, {"type": "connection", "data": c})
            QTreeWidgetItem(item)

    def _open_new_conn_dialog(self):
        dlg = NewConnectionDialog(self)
        if dlg.exec_():
            if self.repository.save_connection(dlg.conn_data):
                self._load_connections()

    def _on_item_expanded(self, item):
        if item.childCount() == 1 and item.child(0).text(0) == "":
            item.removeChild(item.child(0)) 
        else:
            return

        node_data = item.data(0, Qt.UserRole)
        node_type = node_data.get("type")

        if node_type == "connection":
            conn_info = node_data["data"]
            try:
                inspector = DbInspector(conn_info)
                schemas = inspector.get_schemas()
                for schema in schemas:
                    child = QTreeWidgetItem(item)
                    child.setText(0, schema)
                    child.setData(0, Qt.UserRole, {"type": "schema", "name": schema, "conn": conn_info})
                    child.setIcon(0, QIcon("ui/resources/icons/schema.png"))
                    QTreeWidgetItem(child) 
            except Exception as e:
                QMessageBox.critical(self, "Connection Error", str(e))

        elif node_type == "schema":
            conn_info = node_data["conn"]
            schema_name = node_data["name"]
            try:
                inspector = DbInspector(conn_info)
                tables = inspector.get_tables(schema_name)
                for table in tables:
                    child = QTreeWidgetItem(item)
                    child.setText(0, table)
                    child.setData(0, Qt.UserRole, {"type": "table", "schema": schema_name, "name": table, "conn": conn_info})
                    child.setIcon(0, QIcon("ui/resources/icons/table.png"))
            except Exception:
                pass

    def _on_item_clicked(self, item, col):
        node_data = item.data(0, Qt.UserRole)
        if not node_data: return

        if node_data["type"] == "table":
            self.current_schema = node_data["schema"]
            self.current_table = node_data["name"]
            self.active_inspector = DbInspector(node_data["conn"])
            
            self.lbl_table.setText(f"Active Table: {self.current_schema}.{self.current_table}")
            self.le_filter.clear()
            self.btn_load_canvas.setEnabled(False)
            
            self._run_filter_query()

    def _run_filter_query(self):
        """
        Kullanıcının girdiği filtreye göre SQL oluşturur ve çalıştırır.
        """
        if not self.active_inspector or not self.current_table:
            return

        filter_text = self.le_filter.text().strip()
        
        sql = f"SELECT * FROM {self.current_schema}.{self.current_table}"
        if filter_text:
            if not filter_text.upper().startswith("WHERE"):
                sql += f" WHERE {filter_text}"
            else:
                sql += f" {filter_text}"
        
        sql += " LIMIT 10"

        self.result_view.setDisabled(True)
        
        self.worker = DbQueryWorker(self.active_inspector, sql)
        self.worker.finished_success.connect(self._on_query_success)
        self.worker.finished_error.connect(lambda err: QMessageBox.critical(self, "Query Error", err))
        self.worker.finished.connect(lambda: self.result_view.setDisabled(False))
        self.worker.start()

    def _on_query_success(self, df):
        model = QStandardItemModel(df.shape[0], df.shape[1])
        model.setHorizontalHeaderLabels(list(df.columns))
        for row in range(df.shape[0]):
            for col in range(df.shape[1]):
                val = str(df.iat[row, col])
                model.setItem(row, col, QStandardItem(val))
        
        self.result_view.setModel(model)
        self.result_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.btn_load_canvas.setEnabled(True)

    def _on_load_to_canvas(self):
        """
        Filtrelenmiş veriyi DataController üzerinden yükler.
        """
        if not self.active_inspector or not self.current_table: return
        
        where_clause = self.le_filter.text().strip()
        
        try:
            self.data_controller.load_from_database(
                conn_info=self.active_inspector.conn_info,
                schema=self.current_schema,
                table=self.current_table,
                where=where_clause
            )
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _action_import_file(self):
        if not self.active_inspector:
            QMessageBox.warning(self, "Warning", "Please select a schema first.")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Point Cloud (*.las *.laz)")
        if not file_path: return

        table_name, ok = QInputDialog.getText(self, "Table Name", "Enter destination table name:")
        if ok and table_name:
            full_table_name = f"{self.current_schema}.{table_name}" if self.current_schema else table_name
            self.data_controller.import_layer_to_db(
                source_path=file_path, 
                conn_info=self.active_inspector.conn_info, 
                table_name=full_table_name
            )
            QMessageBox.information(self, "Started", "Import process started in background.")