from app import create_app

app = create_app()


def _serve():
    from waitress import serve

    print("\n╭────────────────────────────────────────────╮")
    print("│  ShareCircle · Overlap                    │")
    print("│  Your neighborhood help circle is live.   │")
    print("│                                            │")
    print("│  Local:  http://127.0.0.1:5000           │")
    print("│  LAN:    http://<your-ip>:5000            │")
    print("│  Judge:  /judge?demo=1                    │")
    print("│                                            │")
    print("│  Press Ctrl+C to stop. Have a great run!  │")
    print("╰────────────────────────────────────────────╯\n")
    serve(app, host="0.0.0.0", port=5000)


if __name__ == '__main__':
    _serve()
