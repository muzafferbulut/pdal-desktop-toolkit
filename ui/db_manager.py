from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, 
                             QTreeWidgetItem, QWidget, QTableView, QLineEdit,
                             QPushButton, QLabel, QFormLayout, QDialogButtonBox, 
                             QMessageBox, QHeaderView, QStyle, QToolBar, QAction, 
                             QFileDialog, QInputDialog, QPlainTextEdit, QMenu)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from core.database.inspector import DbInspector
from core.database.repository import Repository
from core.database.workers import DbQueryWorker 

class NewConnectionDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New PostGIS Connection")
        self.resize(300, 280)
        self.conn_data = {}
        self._setup_ui()

    def _setup_ui(self):
        l = QVBoxLayout(self)
        f = QFormLayout()
        self.le_name, self.le_host, self.le_port = QLineEdit("Local DB"), QLineEdit("localhost"), QLineEdit("5432")
        self.le_db, self.le_user, self.le_pass = QLineEdit(), QLineEdit("postgres"), QLineEdit()
        self.le_pass.setEchoMode(QLineEdit.Password)
        f.addRow("Name:", self.le_name); f.addRow("Host:", self.le_host); f.addRow("Port:", self.le_port)
        f.addRow("DB:", self.le_db); f.addRow("User:", self.le_user); f.addRow("Pass:", self.le_pass)
        l.addLayout(f)
        btn_t = QPushButton("Test Connection"); btn_t.clicked.connect(self._on_test); l.addWidget(btn_t)
        bb = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._on_save); bb.rejected.connect(self.reject); l.addWidget(bb)

    def _on_test(self):
        c = {"host": self.le_host.text(), "port": self.le_port.text(), "user": self.le_user.text(), "password": self.le_pass.text(), "dbname": self.le_db.text()}
        try: DbInspector(c).get_schemas(); QMessageBox.information(self, "OK", "Success!")
        except Exception as e: QMessageBox.critical(self, "Err", str(e))

    def _on_save(self):
        self.conn_data = {"name": self.le_name.text(), "host": self.le_host.text(), "port": self.le_port.text(), "database_name": self.le_db.text(), "username": self.le_user.text(), "password": self.le_pass.text(), "db_type": "postgresql"}
        self.accept()

class DbManagerDialog(QDialog):

    def __init__(self, data_controller, parent=None):
        super().__init__(parent)
        self.data_controller, self.repository = data_controller, Repository()
        self.active_inspector, self.current_schema, self.current_table = None, None, None
        self.setWindowTitle("Database Manager"); self.resize(1100, 700); self._setup_ui(); self._load_connections()

    def _setup_ui(self):
        ml = QVBoxLayout(self); tb = QToolBar(); tb.setMovable(False); ml.addWidget(tb)
        tb.addAction(QAction(QIcon("ui/resources/icons/add_connection.png"), "New", self, triggered=self._open_new_conn_dialog))
        tb.addAction(QAction(QIcon("ui/resources/icons/refresh.png"), "Refresh", self, triggered=self._load_connections))
        tb.addSeparator()
        tb.addAction(QAction(QIcon("ui/resources/icons/open.png"), "Import File", self, triggered=self._action_import_file))
        tb.addAction(QAction(QIcon("ui/resources/icons/database.png"), "Export Layer", self, triggered=self._action_export_active_layer))

        sp = QSplitter(Qt.Horizontal); ml.addWidget(sp)
        self.tree = QTreeWidget(); self.tree.setHeaderLabel("Browser"); self.tree.itemExpanded.connect(self._on_item_expanded); self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu); self.tree.customContextMenuRequested.connect(self._show_context_menu)
        sp.addWidget(self.tree)

        rp = QWidget(); rl = QVBoxLayout(rp); sp.addWidget(rp)
        self.lbl_table = QLabel("SQL Editor"); rl.addWidget(self.lbl_table)
        self.sql_editor = QPlainTextEdit(); self.sql_editor.setMaximumHeight(200); rl.addWidget(self.sql_editor)
        
        bl = QHBoxLayout(); rl.addLayout(bl)
        btn_r = QPushButton("Execute SQL"); btn_r.clicked.connect(self._run_sql_query); bl.addWidget(btn_r); bl.addStretch()
        self.btn_load = QPushButton("Load to Canvas"); self.btn_load.setEnabled(False); self.btn_load.clicked.connect(self._on_load_to_canvas); bl.addWidget(self.btn_load)
        
        self.result_view = QTableView(); rl.addWidget(self.result_view); sp.setStretchFactor(1, 3)

    def _show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if item and item.data(0, Qt.UserRole)["type"] == "connection":
            m = QMenu(); a = m.addAction("Delete"); r = m.exec_(self.tree.mapToGlobal(pos))
            if r == a and self.repository.delete_connection(item.data(0, Qt.UserRole)["data"]["id"]): self._load_connections()

    def _load_connections(self):
        self.tree.clear()
        for c in self.repository.get_connections():
            i = QTreeWidgetItem(self.tree, [c["name"]]); i.setIcon(0, self.style().standardIcon(QStyle.SP_DriveNetIcon))
            i.setData(0, Qt.UserRole, {"type": "connection", "data": c}); QTreeWidgetItem(i)

    def _open_new_conn_dialog(self):
        dlg = NewConnectionDialog(self)
        if dlg.exec_() and self.repository.save_connection(dlg.conn_data): self._load_connections()

    def _on_item_expanded(self, i):
        if i.childCount() == 1 and i.child(0).text(0) == "": i.removeChild(i.child(0))
        else: return
        d = i.data(0, Qt.UserRole)
        try:
            insp = DbInspector(d["data"] if d["type"] == "connection" else d["conn"])
            if d["type"] == "connection":
                for s in insp.get_schemas():
                    if s in ["information_schema", "pg_catalog"]: continue
                    c = QTreeWidgetItem(i, [s]); c.setData(0, Qt.UserRole, {"type": "schema", "name": s, "conn": d["data"]}); c.setIcon(0, QIcon("ui/resources/icons/schema.png")); QTreeWidgetItem(c)
            elif d["type"] == "schema":
                for t in insp.get_tables(d["name"]):
                    c = QTreeWidgetItem(i, [t]); c.setData(0, Qt.UserRole, {"type": "table", "schema": d["name"], "name": t, "conn": d["conn"]}); c.setIcon(0, QIcon("ui/resources/icons/table.png"))
        except Exception as e: QMessageBox.critical(self, "Err", str(e))

    def _on_item_clicked(self, i, c):
        d = i.data(0, Qt.UserRole)
        if d.get("type") == "table":
            self.current_schema, self.current_table, self.active_inspector = d["schema"], d["name"], DbInspector(d["conn"])
            self.lbl_table.setText(f"Active Table: {self.current_schema}.{self.current_table}")
            self.sql_editor.setPlainText(f"SELECT * FROM {self.current_schema}.{self.current_table} LIMIT 100")
            self.btn_load.setEnabled(False)

    def _run_sql_query(self):
        if not self.active_inspector: return
        self.result_view.setDisabled(True)
        self.w = DbQueryWorker(self.active_inspector, self.sql_editor.toPlainText())
        self.w.finished_success.connect(self._on_query_success); self.w.finished_error.connect(lambda e: QMessageBox.critical(self, "Err", e))
        self.w.finished.connect(lambda: self.result_view.setDisabled(False)); self.w.start()

    def _on_query_success(self, df):
        m = QStandardItemModel(df.shape[0], df.shape[1]); m.setHorizontalHeaderLabels(list(df.columns))
        for r in range(df.shape[0]):
            for c in range(df.shape[1]): m.setItem(r, c, QStandardItem(str(df.iat[r, c])))
        self.result_view.setModel(m); self.btn_load.setEnabled(True)

    def _on_load_to_canvas(self):
        sql = self.sql_editor.toPlainText().lower(); wh = sql.split("where")[-1].split("limit")[0].strip() if "where" in sql else ""
        self.data_controller.load_from_database(self.active_inspector.conn_info, self.current_schema, self.current_table, wh); self.close()

    def _action_import_file(self):
        if not self.current_table or not self.active_inspector.validate_pc_table(self.current_schema, self.current_table): return
        f, _ = QFileDialog.getOpenFileName(self, "Open", "", "*.las *.laz")
        if f: self.data_controller.import_layer_to_db(f, self.active_inspector.conn_info, self.current_schema, self.current_table)

    def _action_export_active_layer(self):
        if self.current_table and self.active_inspector.validate_pc_table(self.current_schema, self.current_table):
            self.data_controller.export_active_layer_to_db(self.active_inspector.conn_info, self.current_schema, self.current_table)