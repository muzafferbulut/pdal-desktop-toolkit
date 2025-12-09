from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, 
                             QTreeWidgetItem, QWidget, QTabWidget, QTableView, QPlainTextEdit,
                             QPushButton, QLabel, QFormLayout, QLineEdit, QDialogButtonBox, 
                             QMessageBox, QHeaderView, QStyle)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
from core.database.inspector import DbInspector
from core.database.repository import Repository

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
    """
    Veritabanı yöneticisi ana penceresi.
    Sol panelde ağaç yapısı (Connection -> Schema -> Table/View),
    Sağ panelde veri önizleme ve SQL editörü bulunur.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database Manager")
        self.resize(1000, 650)
        self.repository = Repository()
        self.active_inspector = None
        self.current_schema = None
        self.current_table = None
        
        self._setup_ui()
        self._load_connections()

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        top_bar = QHBoxLayout()
        btn_new_conn = QPushButton("New Connection")
        btn_new_conn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        btn_new_conn.clicked.connect(self._open_new_conn_dialog)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        btn_refresh.clicked.connect(self._load_connections)

        top_bar.addWidget(btn_new_conn)
        top_bar.addWidget(btn_refresh)
        top_bar.addStretch()
        main_layout.addLayout(top_bar)
        splitter = QSplitter(Qt.Horizontal)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Browser")
        self.tree.itemExpanded.connect(self._on_item_expanded)
        self.tree.itemClicked.connect(self._on_item_clicked)
        splitter.addWidget(self.tree)

        self.tabs = QTabWidget()
        
        self.tab_info = QWidget()
        info_layout = QVBoxLayout()
        self.table_view = QTableView()
        info_layout.addWidget(QLabel("Data Preview (First 10 rows):"))
        info_layout.addWidget(self.table_view)
        self.tab_info.setLayout(info_layout)
        
        self.tab_sql = QWidget()
        sql_layout = QVBoxLayout()
        self.sql_editor = QPlainTextEdit()
        self.sql_editor.setPlaceholderText("SELECT * FROM ...")
        
        btn_run_sql = QPushButton("Execute")
        btn_run_sql.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        btn_run_sql.clicked.connect(self._run_custom_sql)
        
        self.sql_result_view = QTableView()
        
        sql_layout.addWidget(QLabel("Query:"))
        sql_layout.addWidget(self.sql_editor)
        sql_layout.addWidget(btn_run_sql)
        sql_layout.addWidget(QLabel("Result:"))
        sql_layout.addWidget(self.sql_result_view)
        self.tab_sql.setLayout(sql_layout)

        self.tabs.addTab(self.tab_info, "Table Info")
        self.tabs.addTab(self.tab_sql, "SQL Window")
        
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(1, 1)
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
            # --- Bağlantı ise ŞEMALARI yükle ---
            conn_info = node_data["data"]
            try:
                inspector = DbInspector(conn_info)
                schemas = inspector.get_schemas()
                for schema in schemas:
                    child = QTreeWidgetItem(item)
                    child.setText(0, schema)
                    child.setData(0, Qt.UserRole, {
                        "type": "schema", 
                        "name": schema, 
                        "conn": conn_info
                    })
                    # Şema İkonu
                    child.setIcon(0, QIcon("ui/resources/icons/schema.png"))
                    QTreeWidgetItem(child) # Dummy item (altında tablolar olacak)
            except Exception as e:
                QMessageBox.critical(self, "Connection Error", str(e))

        elif node_type == "schema":
            # --- Şema ise TABLO ve VIEW'ları yükle ---
            conn_info = node_data["conn"]
            schema_name = node_data["name"]
            
            try:
                inspector = DbInspector(conn_info)
                
                # 1. Tablolar
                tables = inspector.get_tables(schema_name)
                for table in tables:
                    child = QTreeWidgetItem(item)
                    child.setText(0, table)
                    child.setData(0, Qt.UserRole, {
                        "type": "table", 
                        "schema": schema_name, 
                        "name": table, 
                        "conn": conn_info
                    })
                    # Tablo İkonu
                    child.setIcon(0, QIcon("ui/resources/icons/table.png"))

                # 2. View'lar
                views = inspector.get_views(schema_name)
                for view in views:
                    child = QTreeWidgetItem(item)
                    child.setText(0, view)
                    child.setData(0, Qt.UserRole, {
                        "type": "view", 
                        "schema": schema_name, 
                        "name": view, 
                        "conn": conn_info
                    })
                    # View İkonu
                    child.setIcon(0, QIcon("ui/resources/icons/view.png"))
            
            except Exception as e:
                # Şema boşsa veya erişim hatası varsa kullanıcıyı yormadan logla veya geç
                print(f"Error loading schema contents: {e}")

    def _on_item_clicked(self, item, col):
        node_data = item.data(0, Qt.UserRole)
        if not node_data: return

        if node_data["type"] in ["table", "view"]:
            self.current_schema = node_data["schema"]
            self.current_table = node_data["name"]
            self.active_inspector = DbInspector(node_data["conn"])
            sql = f"SELECT * FROM {self.current_schema}.{self.current_table} LIMIT 10"
            self._execute_sql_to_view(sql, self.table_view)
            self.tabs.setCurrentIndex(0)

    def _run_custom_sql(self):
        sql = self.sql_editor.toPlainText()
        if not sql:
            return

        if not self.active_inspector:
            QMessageBox.warning(self, "No Connection", "Please select a table/schema from the tree to establish context first.")
            return

        self._execute_sql_to_view(sql, self.sql_result_view)

    def _execute_sql_to_view(self, sql, view_widget):
        if not self.active_inspector: return
        
        result = self.active_inspector.execute_query(sql)
        if result["status"]:
            df = result["data"]
            model = QStandardItemModel(df.shape[0], df.shape[1])
            model.setHorizontalHeaderLabels(df.columns)
            
            for row in range(df.shape[0]):
                for col in range(df.shape[1]):
                    val = str(df.iat[row, col])
                    model.setItem(row, col, QStandardItem(val))
            
            view_widget.setModel(model)
            view_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        else:
            QMessageBox.critical(self, "SQL Error", result["error"])