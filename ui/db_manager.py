from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, 
                             QTreeWidgetItem, QWidget, QTableView, QLineEdit,
                             QPushButton, QLabel, QFormLayout, QDialogButtonBox, 
                             QMessageBox, QStyle, QToolBar, QAction, 
                             QFileDialog, QInputDialog, QPlainTextEdit, QMenu)
from PyQt5.QtGui import (QIcon, QStandardItemModel, QStandardItem, QSyntaxHighlighter, 
                         QTextCharFormat, QColor, QFont)
from PyQt5.QtCore import Qt
from core.database.inspector import DbInspector
from core.database.repository import Repository
from core.database.workers import DbQueryWorker 
import re
import os

class SqlHighlighter(QSyntaxHighlighter):
    """SQL sözdizimini renklendiren yardımcı sınıf."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []

        # SQL Anahtar Kelimeleri (Mavi ve Kalın)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#3498db"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            r"\bSELECT\b", r"\bFROM\b", r"\bWHERE\b", r"\bAND\b", r"\bOR\b", 
            r"\bLIMIT\b", r"\bGROUP BY\b", r"\bORDER BY\b", r"\bAS\b",
            r"\bDISTINCT\b", r"\bJOIN\b", r"\bON\b", r"\bDESC\b", r"\bASC\b"
        ]
        for kw in keywords: 
            self.rules.append((re.compile(kw, re.IGNORECASE), keyword_format))

        # PointCloud & PostGIS Fonksiyonları (Mor)
        func_format = QTextCharFormat()
        func_format.setForeground(QColor("#9b59b6"))
        funcs = [
            r"\bPC_Intersects\b", r"\bPC_Get\b", r"\bPC_Patch\b", 
            r"\bST_MakeEnvelope\b", r"\bPC_Summary\b", r"\bPC_Explode\b",
            r"\bST_Transform\b", r"\bPC_FilterEquals\b", r"\bPC_FilterBetween\b"
        ]
        for f in funcs: 
            self.rules.append((re.compile(f, re.IGNORECASE), func_format))

        # Sayılar (Turuncu)
        num_format = QTextCharFormat()
        num_format.setForeground(QColor("#e67e22"))
        self.rules.append((re.compile(r"\b[0-9.]+\b"), num_format))

    def highlightBlock(self, text):
        for pattern, format in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), format)

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
        try: 
            DbInspector(c).get_schemas()
            QMessageBox.information(self, "OK", "Success!")
        except Exception as e: 
            QMessageBox.critical(self, "Err", str(e))

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
        ml = QVBoxLayout(self); tb = QToolBar()
        tb.setMovable(False); ml.addWidget(tb)
        tb.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        tb.addAction(QAction(QIcon("ui/resources/icons/add_connection.png"), "New", self, triggered=self._open_new_conn_dialog))
        tb.addAction(QAction(QIcon("ui/resources/icons/refresh.png"), "Refresh", self, triggered=self._load_connections))
        tb.addSeparator()
        active_path = self.data_controller.active_layer_path
        layer_name = os.path.basename(active_path) if active_path else "No Layer Selected"
        self.action_export = QAction(QIcon("ui/resources/icons/send_to.png"), f" Send to DB '{layer_name}'", self)
        self.action_export.triggered.connect(self._action_export_active_layer)
        tb.addAction(self.action_export)

        sp = QSplitter(Qt.Horizontal); ml.addWidget(sp)
        
        self.tree = QTreeWidget(); self.tree.setHeaderLabel("Browser")
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        sp.addWidget(self.tree)

        rp = QWidget(); rl = QVBoxLayout(rp); sp.addWidget(rp)
        self.lbl_table = QLabel("SQL Editor"); rl.addWidget(self.lbl_table)
        
        self.sql_editor = QPlainTextEdit()
        self.sql_editor.setMaximumHeight(200)
        self.highlighter = SqlHighlighter(self.sql_editor.document()) #
        rl.addWidget(self.sql_editor)

        bl = QHBoxLayout(); rl.addLayout(bl)
        btn_r = QPushButton(" Execute SQL"); btn_r.setIcon(QIcon("ui/resources/icons/run.png"))
        btn_r.clicked.connect(self._run_sql_query); bl.addWidget(btn_r)
        
        self.btn_draw = QPushButton(" Draw Area")
        self.btn_draw.setIcon(QIcon("ui/resources/icons/crop.png"))
        self.btn_draw.setEnabled(False)
        self.btn_draw.clicked.connect(self._on_draw_clicked)
        bl.addWidget(self.btn_draw)

        bl.addStretch()
        
        self.btn_import = QPushButton(" Import From File")
        self.btn_import.setIcon(QIcon("ui/resources/icons/open.png"))
        self.btn_import.setStyleSheet("background-color: #3498db; color: white; font-weight: bold; padding: 5px;")
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self._action_import_file)
        bl.addWidget(self.btn_import)

        self.btn_load = QPushButton(" Add to Canvas"); self.btn_load.setIcon(QIcon("ui/resources/icons/add_to_canvas.png"))
        self.btn_load.setEnabled(False); self.btn_load.clicked.connect(self._on_load_to_canvas); bl.addWidget(self.btn_load)
        
        self.result_view = QTableView(); rl.addWidget(self.result_view); sp.setStretchFactor(1, 3)

    def _on_draw_clicked(self):
        main_win = self.parent()
        if hasattr(main_win, 'map_view'):
            try:
                main_win.map_view.bridge.area_drawn.disconnect(self._inject_spatial_sql)
            except:
                pass
            main_win.map_view.bridge.area_drawn.connect(self._inject_spatial_sql)
            main_win.map_view.page().runJavaScript("window.startDrawingJS();")
            
            self.hide()

    def _inject_spatial_sql(self, minx, miny, maxx, maxy):
        """Koordinatları SQL'e basar ve pencereyi geri getirir."""
        spatial_filter = f"\nAND PC_Intersects(patch, ST_MakeEnvelope({minx:.6f}, {miny:.6f}, {maxx:.6f}, {maxy:.6f}, 4326))"
        self.sql_editor.appendPlainText(spatial_filter)
        
        self.show()
        self.raise_()
        main_win = self.parent()
        try:
            main_win.map_view.bridge.area_drawn.disconnect(self._inject_spatial_sql)
        except:
            pass

    def _on_item_clicked(self, i, c):
        d = i.data(0, Qt.UserRole)
        if d.get("type") in ["table", "view"]:
            self.current_schema, self.current_table, self.active_inspector = d["schema"], d["name"], DbInspector(d["conn"])
            self.lbl_table.setText(f"Active Object: {self.current_schema}.{self.current_table}")
            self.sql_editor.setPlainText(f'SELECT * FROM "{self.current_schema}"."{self.current_table}"')
            self.btn_import.setEnabled(True)
            self.btn_draw.setEnabled(True)
            self.btn_load.setEnabled(False)

    def _load_connections(self):
        self.tree.clear()
        for c in self.repository.get_connections():
            i = QTreeWidgetItem(self.tree, [c["name"]]); i.setIcon(0, self.style().standardIcon(QStyle.SP_DriveNetIcon))
            i.setData(0, Qt.UserRole, {"type": "connection", "data": c}); QTreeWidgetItem(i)

    def _open_new_conn_dialog(self):
        dlg = NewConnectionDialog(self)
        if dlg.exec_() and self.repository.save_connection(dlg.conn_data): self._load_connections()

    def _run_sql_query(self):
        if not self.active_inspector: return
        self.result_view.setDisabled(True)
        self.w = DbQueryWorker(self.active_inspector, self.sql_editor.toPlainText())
        self.w.finished_success.connect(self._on_query_success)
        self.w.finished_error.connect(lambda e: QMessageBox.critical(self, "Error", e))
        self.w.finished.connect(lambda: self.result_view.setDisabled(False)); self.w.start()

    def _on_query_success(self, df):
        m = QStandardItemModel(df.shape[0], df.shape[1]); m.setHorizontalHeaderLabels(list(df.columns))
        for r in range(df.shape[0]):
            for c in range(df.shape[1]): m.setItem(r, c, QStandardItem(str(df.iat[r, c])))
        self.result_view.setModel(m); self.btn_load.setEnabled(True)

    def _on_load_to_canvas(self):
        sql = self.sql_editor.toPlainText().lower()
        wh = sql.split("where")[-1].split("limit")[0].strip() if "where" in sql else ""
        self.data_controller.load_from_database(self.active_inspector.conn_info, self.current_schema, self.current_table, wh)
        self.close()

    def _on_item_expanded(self, i):
        if i.childCount() == 1 and i.child(0).text(0) == "": i.removeChild(i.child(0))
        else: return
        d = i.data(0, Qt.UserRole)
        EXCLUDED = {"spatial_ref_sys", "geometry_columns", "geography_columns", "topology", "pointcloud_formats", "pointcloud_columns"}
        try:
            insp = DbInspector(d["data"] if d["type"] == "connection" else d["conn"])
            if d["type"] == "connection":
                for s in insp.get_schemas():
                    if s.startswith("pg_") or s in ["information_schema"]: continue
                    c = QTreeWidgetItem(i, [s]); c.setData(0, Qt.UserRole, {"type": "schema", "name": s, "conn": d["data"]})
                    c.setIcon(0, QIcon("ui/resources/icons/schema.png")); QTreeWidgetItem(c)
            elif d["type"] == "schema":
                for t in insp.get_tables(d["name"]):
                    if t.lower() in EXCLUDED: continue
                    c = QTreeWidgetItem(i, [t]); c.setData(0, Qt.UserRole, {"type": "table", "schema": d["name"], "name": t, "conn": d["conn"]})
                    c.setIcon(0, QIcon("ui/resources/icons/table.png"))
                for v in insp.get_views(d["name"]):
                    if v.lower() in EXCLUDED: continue
                    c = QTreeWidgetItem(i, [v]); c.setData(0, Qt.UserRole, {"type": "view", "schema": d["name"], "name": v, "conn": d["conn"]})
                    c.setIcon(0, QIcon("ui/resources/icons/view.png"))
        except Exception as e: QMessageBox.critical(self, "Error", f"Browser error: {str(e)}")

    def _show_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item: return
        d = item.data(0, Qt.UserRole)
        menu = QMenu()
        if d["type"] == "connection":
            act_new = menu.addAction(QIcon("ui/resources/icons/add.png"), "New Schema")
            menu.addSeparator()
            act_del = menu.addAction(QIcon("ui/resources/icons/remove.png"), "Delete Connection")
            res = menu.exec_(self.tree.mapToGlobal(pos))
            if res == act_del:
                if self.repository.delete_connection(d["data"]["id"]): self._load_connections()
            elif res == act_new: self._create_new_schema(d["data"])
        elif d["type"] == "schema":
            act_table = menu.addAction(QIcon("ui/resources/icons/table.png"), "New Table")
            res = menu.exec_(self.tree.mapToGlobal(pos))
            if res == act_table: self._create_new_table(d["conn"], d["name"])

    def _create_new_schema(self, conn_info):
        name, ok = QInputDialog.getText(self, "New Schema", "Enter schema name:")
        if ok and name.strip():
            if DbInspector(conn_info).create_schema(name.strip())["status"]: self._load_connections()
            else: QMessageBox.critical(self, "Error", "Could not create schema.")

    def _create_new_table(self, conn_info, schema_name):
        name, ok = QInputDialog.getText(self, "New Table", f"Create table in {schema_name}:")
        if ok and name.strip():
            res = DbInspector(conn_info).create_pc_table(schema_name, name.strip())
            if res["status"]: self._load_connections()
            else: QMessageBox.critical(self, "Error", res.get("error"))

    def _action_import_file(self):
        if not self.current_table or not self.active_inspector.validate_pc_table(self.current_schema, self.current_table): return
        f, _ = QFileDialog.getOpenFileName(self, "Open", "", "*.las *.laz")
        if f: self.data_controller.import_layer_to_db(f, self.active_inspector.conn_info, self.current_schema, self.current_table)

    def _action_export_active_layer(self):
        if self.current_table and self.active_inspector.validate_pc_table(self.current_schema, self.current_table):
            self.data_controller.export_active_layer_to_db(self.active_inspector.conn_info, self.current_schema, self.current_table)