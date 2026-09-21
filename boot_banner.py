"""Paint SuperCalc banner on PicoCalc IPS (picocalcdisplay + framebuf)."""
import framebuf
import picocalcdisplay as pd

W = H = 320
ct = framebuf.GS4_HMSB
buf = bytearray(W * H // 2)
fb = framebuf.FrameBuffer(buf, W, H, ct)
pd.init(buf, ct, True)
pd.beginDraw()
fb.fill(0)
pd.drawTxt6x8("SuperCalc.OG", 20, 40, 15)
pd.drawTxt6x8("Phase 7 — USB REPL ready", 20, 56, 10)
pd.drawTxt6x8(">>> from mp.ui.calc_repl import run_demo", 20, 88, 8)
pd.update()
