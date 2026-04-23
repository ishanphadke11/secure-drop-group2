import socket
import json
import threading
import time

ONLINE_USERS = []

PORT = 50000

def start_listender():
# still need to implement

def broadcast_presence(session, contacts():
# still need to implement

def discover_users(session, contacts):
  global ONLINE_USERS
  ONLINE_USERS = []
  broadcast_presence(session, contacts)
  # wait for a response
  time.sleep(2)
  return ONLINE_USERS
