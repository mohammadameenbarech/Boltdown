"""
Piece and Block Management
Handles piece downloading, verification, and assembly
"""

import hashlib
import os
import threading


class PieceManager:
    """Manages torrent pieces and blocks"""
    
    BLOCK_SIZE = 16384  # 16KB blocks
    
    def __init__(self, torrent_info, save_path):
        self.torrent_info = torrent_info
        self.save_path = save_path
        
        self.num_pieces = torrent_info['num_pieces']
        self.piece_length = torrent_info['piece_length']
        self.total_size = torrent_info['total_size']
        self.pieces_hash = torrent_info['pieces_hash']
        
        # Track piece status
        self.pieces = [{'downloaded': False, 'blocks': {}} for _ in range(self.num_pieces)]
        self.pieces_lock = threading.Lock()
        
        # File handle for writing
        self.file_path = os.path.join(save_path, torrent_info['name'])
        self.file_handle = None
        self._prepare_file()
    
    def _prepare_file(self):
        """Prepare output file"""
        os.makedirs(os.path.dirname(self.file_path) if os.path.dirname(self.file_path) else self.save_path, exist_ok=True)
        self.file_handle = open(self.file_path, 'wb')
        # Pre-allocate file
        self.file_handle.seek(self.total_size - 1)
        self.file_handle.write(b'\x00')
        self.file_handle.flush()
    
    def get_next_request(self):
        """Get next block to request from peers"""
        with self.pieces_lock:
            for piece_index, piece in enumerate(self.pieces):
                if piece['downloaded']:
                    continue
                
                # Find missing blocks in this piece
                piece_size = self._get_piece_size(piece_index)
                num_blocks = (piece_size + self.BLOCK_SIZE - 1) // self.BLOCK_SIZE
                
                for block_index in range(num_blocks):
                    if block_index not in piece['blocks']:
                        offset = block_index * self.BLOCK_SIZE
                        length = min(self.BLOCK_SIZE, piece_size - offset)
                        return (piece_index, offset, length)
        
        return None
    
    def add_block(self, piece_index, offset, data):
        """Add downloaded block and assemble pieces"""
        with self.pieces_lock:
            if piece_index >= len(self.pieces):
                return
            
            block_index = offset // self.BLOCK_SIZE
            self.pieces[piece_index]['blocks'][block_index] = data
            
            # Check if piece is complete
            if self._is_piece_complete(piece_index):
                self._assemble_piece(piece_index)
    
    def _is_piece_complete(self, piece_index):
        """Check if all blocks of a piece are downloaded"""
        piece_size = self._get_piece_size(piece_index)
        num_blocks = (piece_size + self.BLOCK_SIZE - 1) // self.BLOCK_SIZE
        return len(self.pieces[piece_index]['blocks']) == num_blocks
    
    def _assemble_piece(self, piece_index):
        """Assemble and verify piece"""
        piece = self.pieces[piece_index]
        
        # Concatenate blocks in order
        piece_data = b''
        num_blocks = len(piece['blocks'])
        for i in range(num_blocks):
            if i in piece['blocks']:
                piece_data += piece['blocks'][i]
        
        # Verify hash
        piece_hash = hashlib.sha1(piece_data).digest()
        expected_hash = self.pieces_hash[piece_index]
        
        if piece_hash == expected_hash:
            # Write to file
            offset = piece_index * self.piece_length
            self.file_handle.seek(offset)
            self.file_handle.write(piece_data)
            self.file_handle.flush()
            
            piece['downloaded'] = True
            piece['blocks'] = {}  # Free memory
            
            print(f"[+] Piece {piece_index}/{self.num_pieces} verified and written")
        else:
            # Hash mismatch, re-download
            print(f"[!] Piece {piece_index} hash mismatch, re-downloading")
            piece['blocks'] = {}
    
    def _get_piece_size(self, piece_index):
        """Get size of a specific piece"""
        if piece_index == self.num_pieces - 1:
            # Last piece might be smaller
            return self.total_size - (piece_index * self.piece_length)
        return self.piece_length
    
    def get_progress(self):
        """Calculate download progress"""
        with self.pieces_lock:
            downloaded = sum(1 for p in self.pieces if p['downloaded'])
            return (downloaded / self.num_pieces) * 100 if self.num_pieces > 0 else 0
    
    def is_complete(self):
        """Check if download is complete"""
        with self.pieces_lock:
            return all(p['downloaded'] for p in self.pieces)
    
    def close(self):
        """Close file handle"""
        if self.file_handle:
            self.file_handle.close()
