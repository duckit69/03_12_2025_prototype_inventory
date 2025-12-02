import ctypes

DEFAULT_KEY = "FFFFFFFFFFFF"
READER_NAME = b"HID Global OMNIKEY 5422 Smartcard Reader [OMNIKEY 5422CL Smartcard Reader] (IM0P6H01EE) 00 00"

class MifareWriter:
    def __init__(self, lib_path="./libcard.so"):
        self.cardlib = ctypes.CDLL(lib_path)
        self._set_function_signatures()
        self.reader_name = READER_NAME
        self.key = DEFAULT_KEY.encode()
        self.articles = {}

    def _set_function_signatures(self):
        # Function signatures matching card_comm.c (with underscores)
        self.cardlib.list_readers.restype = ctypes.c_char_p
        self.cardlib.get_last_error.restype = ctypes.c_char_p
        
        self.cardlib.connect_reader.argtypes = [ctypes.c_char_p]
        self.cardlib.connect_reader.restype = ctypes.c_int
        
        self.cardlib.read_block_string.argtypes = [ctypes.c_char_p, ctypes.c_int]
        self.cardlib.read_block_string.restype = ctypes.c_char_p
        
        self.cardlib.write_block_string.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p]
        self.cardlib.write_block_string.restype = ctypes.c_int
        
        self.cardlib.cleanup.restype = None

    def connect(self):
        """Connect to the MIFARE reader"""
        # Step 1: Get available readers
        readers = self.cardlib.list_readers().decode("utf-8")
        print(f"Available readers: {readers}")
        
        # Step 2: Check if there's an error
        if "ERROR" in readers:
            raise RuntimeError(f"Cannot list readers: {readers}")
        
        # Step 3: Print the exact reader name we're trying to use
        print(f"Trying to connect to: {self.reader_name.decode()}")
        
        # Step 4: Check if our reader is in the list
        if self.reader_name.decode() not in readers:
            raise RuntimeError(f"Reader name mismatch!\nExpected: {self.reader_name.decode()}\nAvailable: {readers}")
        
        # Step 5: Connect
        result = self.cardlib.connect_reader(self.reader_name)
        if result != 0:
            err = self.cardlib.get_last_error().decode("utf-8")
            raise RuntimeError(f"Connect failed: {err}\n(Make sure card is on reader!)")
        
        return True


    def read_block(self, block_num: int) -> str:
        """Read data from a specific block"""
        result = self.cardlib.read_block_string(self.key, block_num)
        return result.decode('utf-8') if result else "ERROR: Read failed"

    def write_block(self, block_num: int, text: str) -> bool:
        """Write data to a specific block (max 16 bytes)"""
        text = text[:16]  # Truncate to 16 bytes max
        result = self.cardlib.write_block_string(self.key, block_num, text.encode())
        return result == 0

    def write_driver_info(self, driver_name: str) -> bool:
        """Write driver info to blocks 1 and 2"""
        # Split driver name if longer than 16 chars
        part1 = driver_name[:16]
        part2 = driver_name[16:32] if len(driver_name) > 16 else ""
        
        success1 = self.write_block(1, part1)
        success2 = self.write_block(2, part2)
        
        return success1 and success2

    def read_driver_info(self) -> str:
        """Read driver info from blocks 1 and 2"""
        part1 = self.read_block(1)
        part2 = self.read_block(2)
        
        # Clean up the result (remove hex dump if present)
        if "ERROR" in part1:
            return part1
        
        # Extract just the text part (before [Hex:)
        if "[Hex:" in part1:
            part1 = part1.split("[Hex:")[0].strip()
        if "[Hex:" in part2:
            part2 = part2.split("[Hex:")[0].strip()
        
        return (part1 + part2).strip()

    def set_articles(self, articles_dict: dict):
        """Set articles to write"""
        self.articles = articles_dict

    def write_articles(self, start_block: int = 8) -> list:
        """
        Write all articles to card starting from specified block.
        Skips trailer blocks (3, 7, 11, 15, ...).
        Returns list of (block, article, status) tuples.
        """
        results = []
        block = start_block
        
        for article, qty in self.articles.items():
            # Skip trailer blocks (every 4th block starting from 3)
            while (block + 1) % 4 == 0:
                block += 1
            
            text = f"{article}:{qty}"[:16]
            success = self.write_block(block, text)
            status = "OK" if success else "FAIL"
            results.append((block, text, status))
            print(f"Block {block}: {text} → {status}")
            block += 1
        
        return results

    def close(self):
        """Cleanup and disconnect"""
        self.cardlib.cleanup()
