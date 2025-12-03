# interface.py - PyQt5 GUI for RFID Batch → MIFARE Writer
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QGroupBox, QHeaderView, QSpinBox, QMessageBox
)
from PyQt5.QtCore import pyqtSignal, QObject
from api_client import fetch_article
from mifare_writer import MifareWriter

class ArticleSignals(QObject):
    article_added = pyqtSignal(str)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.signals = ArticleSignals()
        self.articles = {}
        self.writer = None
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        self.setWindowTitle("RFID Batch → MIFARE Writer")
        self.setGeometry(100, 100, 950, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # ═══════════════════════════════════════════════════════════
        # 1. RFID SCANNING SECTION
        # ═══════════════════════════════════════════════════════════
        scan_group = QGroupBox("1. Scan RFID Tags (125kHz)")
        scan_layout = QVBoxLayout(scan_group)

        rfid_layout = QHBoxLayout()
        self.rfid_input = QLineEdit()
        self.rfid_input.setPlaceholderText("RFID reader types here → Press Enter")
        self.rfid_input.returnPressed.connect(self.scan_rfid_input)
        self.rfid_input.setStyleSheet("font-size: 16px; padding: 10px;")
        rfid_layout.addWidget(QLabel("RFID Tag:"))
        rfid_layout.addWidget(self.rfid_input)

        self.clear_btn = QPushButton("Clear Table")
        self.clear_btn.clicked.connect(self.clear_articles)
        rfid_layout.addWidget(self.clear_btn)

        scan_layout.addLayout(rfid_layout)
        layout.addWidget(scan_group)

        # ═══════════════════════════════════════════════════════════
        # 2. ARTICLES TABLE
        # ═══════════════════════════════════════════════════════════
        table_group = QGroupBox("2. Scanned Articles")
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Article", "Quantity", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.setRowCount(0)
        table_layout.addWidget(self.table)

        layout.addWidget(table_group)

        # ═══════════════════════════════════════════════════════════
        # 3. DRIVER INFO SECTION (Blocks 1 + 2)
        # ═══════════════════════════════════════════════════════════
        driver_group = QGroupBox("3. Driver Information (Blocks 1 + 2)")
        driver_layout = QHBoxLayout(driver_group)

        self.driver_input = QLineEdit()
        self.driver_input.setPlaceholderText("Driver name (max 32 chars)")
        self.driver_input.setMaxLength(32)
        driver_layout.addWidget(QLabel("Driver:"))
        driver_layout.addWidget(self.driver_input)

        self.write_driver_btn = QPushButton("Write Driver Info")
        self.write_driver_btn.clicked.connect(self.write_driver_info)
        self.write_driver_btn.setEnabled(False)
        driver_layout.addWidget(self.write_driver_btn)

        self.read_driver_btn = QPushButton("Read Driver Info")
        self.read_driver_btn.clicked.connect(self.read_driver_info)
        self.read_driver_btn.setEnabled(False)
        driver_layout.addWidget(self.read_driver_btn)

        layout.addWidget(driver_group)

        # ═══════════════════════════════════════════════════════════
        # 4. READ DATA BLOCK SECTION
        # ═══════════════════════════════════════════════════════════
        read_group = QGroupBox("4. Read Data from Card")
        read_layout = QHBoxLayout(read_group)

        self.block_read_input = QSpinBox()
        self.block_read_input.setRange(0, 255)
        self.block_read_input.setValue(4)
        read_layout.addWidget(QLabel("Block:"))
        read_layout.addWidget(self.block_read_input)

        self.read_block_btn = QPushButton("Read Block")
        self.read_block_btn.clicked.connect(self.read_block_data)
        self.read_block_btn.setEnabled(False)
        read_layout.addWidget(self.read_block_btn)

        self.read_result = QLineEdit()
        self.read_result.setReadOnly(True)
        self.read_result.setPlaceholderText("Block data will appear here")
        read_layout.addWidget(QLabel("Data:"))
        read_layout.addWidget(self.read_result)

        layout.addWidget(read_group)

        # ═══════════════════════════════════════════════════════════
        # 5. WRITE TO MIFARE CARD SECTION
        # ═══════════════════════════════════════════════════════════
        write_group = QGroupBox("5. Write Articles to MIFARE Card")
        write_layout = QHBoxLayout(write_group)

        self.block_start_input = QSpinBox()
        self.block_start_input.setRange(4, 255)
        self.block_start_input.setValue(8)
        write_layout.addWidget(QLabel("Start Block:"))
        write_layout.addWidget(self.block_start_input)

        self.connect_btn = QPushButton("Connect Reader")
        self.connect_btn.clicked.connect(self.connect_reader)
        write_layout.addWidget(self.connect_btn)

        self.write_btn = QPushButton("WRITE ALL ARTICLES")
        self.write_btn.clicked.connect(self.write_to_card)
        self.write_btn.setEnabled(False)
        self.write_btn.setStyleSheet("font-weight: bold;")
        write_layout.addWidget(self.write_btn)

        layout.addWidget(write_group)

        # ═══════════════════════════════════════════════════════════
        # 6. STATUS BAR
        # ═══════════════════════════════════════════════════════════
        self.status_label = QLabel("Ready - Click 'Connect Reader' then scan RFID tags")
        self.status_label.setStyleSheet("padding: 10px; background: #f0f0f0; border-radius: 5px;")
        layout.addWidget(self.status_label)

    def connect_signals(self):
        self.signals.article_added.connect(self.add_article)

    def scan_rfid_input(self):
        """Handle RFID input - fetch article and add to table"""
        tag_id = self.rfid_input.text().strip()
        if tag_id:
            article = fetch_article(tag_id)
            if article:
                self.signals.article_added.emit(article)
            else:
                self.status_label.setText(f"❌ Unknown RFID tag: {tag_id}")

            self.rfid_input.clear()
            self.rfid_input.setFocus()

    def add_article(self, article: str):
        """Add article to table, increment quantity if exists"""
        if article in self.articles:
            self.articles[article] += 1
        else:
            self.articles[article] = 1

        self.update_table()
        total_items = sum(self.articles.values())
        self.status_label.setText(
            f"✓ Added: {article} | Unique: {len(self.articles)} | Total items: {total_items}"
        )

    def update_table(self):
        """Refresh the articles table"""
        self.table.setRowCount(len(self.articles))
        row = 0
        for article, qty in self.articles.items():
            self.table.setItem(row, 0, QTableWidgetItem(article))
            self.table.setItem(row, 1, QTableWidgetItem(str(qty)))

            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda _, a=article: self.remove_article(a))
            self.table.setCellWidget(row, 2, remove_btn)
            row += 1

    def remove_article(self, article: str):
        """Remove article from table"""
        if article in self.articles:
            del self.articles[article]
            self.update_table()
            self.status_label.setText(f"Removed: {article}")

    def clear_articles(self):
        """Clear all articles from table"""
        self.articles.clear()
        self.update_table()
        self.status_label.setText("Table cleared")

    # ─────────────────────────────────────────────────────────────────
    # READER CONNECTION
    # ─────────────────────────────────────────────────────────────────
    def connect_reader(self):
        """Connect to MIFARE reader"""
        try:
            self.writer = MifareWriter()
            self.writer.connect()
            
            # Enable all buttons that need reader connection
            self.write_btn.setEnabled(True)
            self.write_driver_btn.setEnabled(True)
            self.read_driver_btn.setEnabled(True)
            self.read_block_btn.setEnabled(True)
            
            self.status_label.setText("✅ Connected to OMNIKEY 5422CL Contactless")
        except Exception as e:
            self.status_label.setText(f"❌ Reader connect failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # DRIVER INFO (Blocks 1 + 2)
    # ─────────────────────────────────────────────────────────────────
    def write_driver_info(self):
        """Write driver name to blocks 1 and 2"""
        if not self.writer:
            return

        driver_name = self.driver_input.text().strip()
        if not driver_name:
            self.status_label.setText("❌ Enter driver name first")
            return

        try:
            success = self.writer.write_driver_info(driver_name)
            if success:
                self.status_label.setText(f"✅ Driver info written: {driver_name}")
            else:
                self.status_label.setText("❌ Failed to write driver info")
        except Exception as e:
            self.status_label.setText(f"❌ Write driver failed: {e}")

    def read_driver_info(self):
        """Read driver info from blocks 1 and 2"""
        if not self.writer:
            return

        try:
            driver_info = self.writer.read_driver_info()
            self.driver_input.setText(driver_info)
            self.status_label.setText(f"✅ Driver info read: {driver_info}")
        except Exception as e:
            self.status_label.setText(f"❌ Read driver failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # READ BLOCK DATA
    # ─────────────────────────────────────────────────────────────────
    def read_block_data(self):
        """Read data from specified block"""
        if not self.writer:
            return

        try:
            block_num = self.block_read_input.value()
            data = self.writer.read_block(block_num)
            self.read_result.setText(data)
            self.status_label.setText(f"✅ Read block {block_num}")
        except Exception as e:
            self.status_label.setText(f"❌ Read failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # WRITE ARTICLES TO CARD
    # ─────────────────────────────────────────────────────────────────
    def write_to_card(self):
        """Write all articles to MIFARE card"""
        if not self.writer or not self.articles:
            self.status_label.setText("❌ Connect reader and scan articles first")
            return

        try:
            start_block = self.block_start_input.value()
            self.writer.set_articles(self.articles)
            results = self.writer.write_articles(start_block)

            # Count successes
            success_count = sum(1 for _, _, status in results if status == "OK")
            total = len(results)

            self.status_label.setText(
                f"✅ Written {success_count}/{total} articles starting at block {start_block}"
            )

            # Show details in message box
            details = "\n".join([f"Block {b}: {t} [{s}]" for b, t, s in results])
            QMessageBox.information(self, "Write Complete", details)

        except Exception as e:
            self.status_label.setText(f"❌ Write failed: {e}")

    # ─────────────────────────────────────────────────────────────────
    # CLEANUP
    # ─────────────────────────────────────────────────────────────────
    def closeEvent(self, event):
        """Cleanup when closing"""
        if self.writer:
            try:
                self.writer.close()
            except:
                pass
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())