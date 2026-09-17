"""Tarayıcıyı açar ve kullanıcı elle giriş yapana kadar bekler (Faz 8, K-006).

Giriş **kullanıcıya aittir**: şifre bu kodda ne istenir, ne yazılır, ne okunur, ne saklanır.
Program yalnızca oturum çerezinin oluşup oluşmadığına bakar (çerezin değerine değil) ve
oluşunca kapanır. Oturum `browser-profile/` altında kalır; klasör gitignore'da.

Kullanım:
    python -m flybrain.insta.login
"""

import argparse
import time

from flybrain.insta.browser import HOME, PROFILE, Browser


def wait_for_login(timeout_s: float = 900.0, poll_s: float = 2.0) -> bool:
    b = Browser(headless=False).open()
    try:
        b.goto(HOME, wait_ms=2000)
        if b.logged_in():
            print("oturum zaten açık.")
            return True
        print("Açılan tarayıcıda Instagram'a gir. Şifreni yalnızca oraya yaz; bu program görmez.")
        print(f"(en fazla {timeout_s / 60:.0f} dakika bekleniyor; pencereyi kapatma)")
        t0 = time.time()
        while time.time() - t0 < timeout_s:
            if b.logged_in():
                print(f"giriş algılandı ({time.time() - t0:.0f} sn). Oturum {PROFILE} içinde saklandı.")
                b.page.wait_for_timeout(2000)  # çerezlerin diske yazılması
                return True
            b.page.wait_for_timeout(int(poll_s * 1000))
        print("süre doldu: giriş algılanmadı.")
        return False
    finally:
        b.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sure", type=float, default=900.0, help="en fazla bekleme (saniye)")
    args = ap.parse_args()
    raise SystemExit(0 if wait_for_login(args.sure) else 1)


if __name__ == "__main__":
    main()
