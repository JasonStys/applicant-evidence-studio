"""Jason Stys: frozen application entry for the private-account native owner window.

The native_desktop module owns the listener, profile lock and graceful shutdown.
The existing WebCrypto browser application and vault format are unchanged.
"""

# Index: main@9

from app.native_desktop import main

if __name__ == "__main__":
    raise SystemExit(main())
