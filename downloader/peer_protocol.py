"""
BitTorrent Peer Wire Protocol Implementation
Handles peer connections, piece requests, and data transfer
"""

import socket
import struct
import threading
import time
from collections import deque


class PeerConnection:
    """Manages connection to a single peer"""
    
    def __init__(self, peer_ip, peer_port, info_hash, peer_id, piece_manager):
        self.peer_ip = peer_ip
        self.peer_port = peer_port
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.piece_manager = piece_manager
        
        self.socket = None
        self.connected = False
        self.choked = True
        self.interested = False
        self.peer_choking = True
        self.peer_interested = False
        
        self.bitfield = None
        self.pending_requests = deque()
        self.running = False
        
        self.downloaded_bytes = 0
    
    def connect(self):
        """Establish connection to peer"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(15)
            
            print(f"[+] Connecting to peer {self.peer_ip}:{self.peer_port}...")
            self.socket.connect((self.peer_ip, self.peer_port))
            
            # Send handshake
            handshake = self._build_handshake()
            self.socket.sendall(handshake)
            
            # Receive handshake response (need exactly 68 bytes)
            response = b''
            while len(response) < 68:
                chunk = self.socket.recv(68 - len(response))
                if not chunk:
                    raise Exception("Peer closed connection during handshake")
                response += chunk
            
            if len(response) == 68:
                self.connected = True
                self.socket.settimeout(30)  # Longer timeout for data transfer
                print(f"[+] Handshake successful with {self.peer_ip}:{self.peer_port}")
                return True
            else:
                print(f"[!] Invalid handshake from {self.peer_ip}")
                return False
            
        except Exception as e:
            print(f"[!] Connection to {self.peer_ip}:{self.peer_port} failed: {e}")
            return False
    
    def _build_handshake(self):
        """Build BitTorrent handshake message"""
        protocol = b"BitTorrent protocol"
        pstr_len = bytes([len(protocol)])
        reserved = b'\x00' * 8
        info_hash_bytes = bytes.fromhex(self.info_hash)
        peer_id_bytes = self.peer_id
        
        return pstr_len + protocol + reserved + info_hash_bytes + peer_id_bytes
    
    def send_interested(self):
        """Send interested message"""
        try:
            msg = struct.pack(">IB", 1, 2)  # length=1, id=2 (interested)
            self.socket.sendall(msg)
            self.interested = True
            print(f"[+] Sent INTERESTED to {self.peer_ip}")
        except Exception as e:
            print(f"[!] Error sending interested: {e}")
    
    def send_request(self, piece_index, block_offset, block_length):
        """Request a block from peer"""
        try:
            msg_id = 6  # request
            payload = struct.pack(">III", piece_index, block_offset, block_length)
            length = 1 + len(payload)
            msg = struct.pack(">IB", length, msg_id) + payload
            self.socket.sendall(msg)
            # print(f"[+] Requested piece {piece_index} block at offset {block_offset}")
        except Exception as e:
            print(f"[!] Error sending request: {e}")
            self.connected = False
    
    def handle_messages(self):
        """Process incoming messages from peer"""
        self.running = True
        
        try:
            while self.running and self.connected:
                # Read message length (4 bytes)
                length_bytes = self._recv_exact(4)
                if not length_bytes:
                    print(f"[!] Peer {self.peer_ip} closed connection")
                    break
                
                length = struct.unpack(">I", length_bytes)[0]
                
                if length == 0:  # Keep-alive
                    continue
                
                # Read message ID (1 byte)
                msg_id_bytes = self._recv_exact(1)
                if not msg_id_bytes:
                    break
                
                msg_id = struct.unpack("B", msg_id_bytes)[0]
                
                # Read payload
                payload_length = length - 1
                payload = b''
                
                if payload_length > 0:
                    payload = self._recv_exact(payload_length)
                    if not payload or len(payload) != payload_length:
                        print(f"[!] Incomplete payload from {self.peer_ip}")
                        break
                
                self._handle_message(msg_id, payload)
                
        except socket.timeout:
            print(f"[!] Timeout reading from {self.peer_ip}")
        except Exception as e:
            print(f"[!] Error in message loop for {self.peer_ip}: {e}")
        finally:
            self.close()
    
    def _recv_exact(self, num_bytes):
        """Receive exactly num_bytes from socket"""
        data = b''
        while len(data) < num_bytes:
            try:
                chunk = self.socket.recv(num_bytes - len(data))
                if not chunk:
                    return None
                data += chunk
            except socket.timeout:
                if len(data) == 0:
                    raise
                continue
            except Exception as e:
                print(f"[!] Error receiving data: {e}")
                return None
        return data
    
    def _handle_message(self, msg_id, payload):
        """Handle different message types"""
        try:
            if msg_id == 0:  # choke
                self.peer_choking = True
                print(f"[!] CHOKED by {self.peer_ip}")
                
            elif msg_id == 1:  # unchoke
                self.peer_choking = False
                print(f"[+] UNCHOKED by {self.peer_ip} - can now download!")
                
            elif msg_id == 2:  # interested
                self.peer_interested = True
                
            elif msg_id == 3:  # not interested
                self.peer_interested = False
                
            elif msg_id == 4:  # have
                if len(payload) >= 4:
                    piece_index = struct.unpack(">I", payload)[0]
                    # print(f"[+] Peer {self.peer_ip} has piece {piece_index}")
                
            elif msg_id == 5:  # bitfield
                self.bitfield = payload
                print(f"[+] Received bitfield from {self.peer_ip} ({len(payload)} bytes)")
                
            elif msg_id == 7:  # piece
                if len(payload) >= 8:
                    index, offset = struct.unpack(">II", payload[:8])
                    block_data = payload[8:]
                    
                    self.downloaded_bytes += len(block_data)
                    print(f"[+] Received piece {index} block (offset {offset}, size {len(block_data)}) from {self.peer_ip}")
                    
                    # Add to piece manager
                    self.piece_manager.add_block(index, offset, block_data)
                else:
                    print(f"[!] Invalid piece message from {self.peer_ip}")
                    
        except Exception as e:
            print(f"[!] Error handling message type {msg_id} from {self.peer_ip}: {e}")
    
    def close(self):
        """Close connection to peer"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        print(f"[+] Closed connection to {self.peer_ip} (downloaded {self.downloaded_bytes} bytes)")

