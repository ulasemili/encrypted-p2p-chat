import socket
import threading


LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 6060

TARGET_HOST = "127.0.0.1"
TARGET_PORT = 5050


def forward(source, destination, direction):
    while True:
        try:
            data = source.recv(4096)

            if not data:
                break

            print("\n==============================")
            print(f"[{direction}] Yakalanan veri:")
            print(data.decode("utf-8", errors="replace"))
            print("==============================\n")

            destination.sendall(data)

        except Exception as e:
            print(f"[HATA] {direction}: {e}")
            break

    source.close()
    destination.close()


def start_proxy():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((LISTEN_HOST, LISTEN_PORT))
    server.listen(1)

    print(f"[SNIFFER] Dinleniyor: {LISTEN_HOST}:{LISTEN_PORT}")
    print(f"[SNIFFER] Yönlendirilecek hedef: {TARGET_HOST}:{TARGET_PORT}")
    print("[SNIFFER] Bağlantı bekleniyor...")

    client_socket, client_address = server.accept()
    print(f"[SNIFFER] Bağlanan kişi: {client_address}")

    target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    target_socket.connect((TARGET_HOST, TARGET_PORT))
    print("[SNIFFER] Gerçek hedefe bağlandı.")

    threading.Thread(
        target=forward,
        args=(client_socket, target_socket, "İstemci -> Hedef"),
        daemon=True
    ).start()

    threading.Thread(
        target=forward,
        args=(target_socket, client_socket, "Hedef -> İstemci"),
        daemon=True
    ).start()

    while True:
        pass


if __name__ == "__main__":
    start_proxy()