"""Ekspor Word (.docx): Daftar Pengeluaran Riil, Surat Pernyataan, Kalkulasi Biaya."""
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from .calc import Result, Settings, Trip, bulatkan, hitung, rentang_tgl, rp, tgl_id

FONT = "Arial"


def _run(p, text, size=11, bold=False, underline=False):
    r = p.add_run(text)
    r.font.name = FONT
    r._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    r.font.size = Pt(size)
    r.bold = bold
    r.underline = underline
    return r


def para(doc, text="", size=11, bold=False, underline=False, align=None, after=2, before=0):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_after, pf.space_before = Pt(after), Pt(before)
    if align == "c":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "r":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if text:
        _run(p, text, size, bold, underline)
    return p


def cell_text(cell, text, size=10, bold=False, align=None, underline=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    p.paragraph_format.space_before = Pt(1)
    if align == "r":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    elif align == "c":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _run(p, text, size, bold, underline)


def set_borders(table, inner=True, outer=True):
    tbl = table._tbl
    pr = tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        on = (inner if edge.startswith("inside") else outer)
        e.set(qn("w:val"), "single" if on else "nil")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:color"), "000000")
        b.append(e)
    pr.append(b)


def widths(table, ws_cm):
    table.autofit = False
    tblPr = table._tbl.tblPr
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblPr.append(lay)
    for i, w in enumerate(ws_cm):
        table.columns[i].width = Cm(w)
    for row in table.rows:
        for i, w in enumerate(ws_cm):
            if i < len(row.cells):
                row.cells[i].width = Cm(w)


def ident_block(doc, rows, size=11):
    t = doc.add_table(rows=len(rows), cols=3)
    for i, (a, b, bold) in enumerate(rows):
        cell_text(t.cell(i, 0), a, size)
        cell_text(t.cell(i, 1), ":", size)
        cell_text(t.cell(i, 2), b, size, bold)
    widths(t, [2.6, 0.5, 13.4])
    return t


def signature(doc, left, right, size=11):
    """left/right = (baris_atas [..], nama, nip)"""
    t = doc.add_table(rows=1, cols=2)
    n_top = max(len(left[0]), len(right[0]))
    left = (left[0] + [" "] * (n_top - len(left[0])),) + tuple(left[1:])
    right = (right[0] + [" "] * (n_top - len(right[0])),) + tuple(right[1:])
    for cell, (top, nama, nip) in zip(t.rows[0].cells, (left, right)):
        cell.text = ""
        first = True
        for line in top:
            p = cell.paragraphs[0] if first else cell.add_paragraph()
            first = False
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_after = Pt(0)
            _run(p, line, size, bold=False)
        for _ in range(3):
            cell.add_paragraph().paragraph_format.space_after = Pt(0)
        p = cell.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(0)
        _run(p, nama, size, True, True)
        if nip:
            p = cell.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            _run(p, nip, size)
    widths(t, [8.2, 8.2])


def calc_text(ln):
    return f"{ln.qty:g} {ln.unit} x Rp {rp(ln.harga)}"


# ------------------------------------------------------------------ dokumen 1
def doc_dp_riil(doc, trip: Trip, res: Result, st: Settings):
    para(doc, "DAFTAR PENGELUARAN RILL", 16, True, True, "c", after=14)
    para(doc, "Yang bertanda tangan dibawah ini :", 11, after=6)
    ident_block(doc, [("Nama", trip.nama.upper(), True), ("NIP", trip.nip or "-", False),
                      ("Jabatan", trip.jabatan_dok.upper(), True)])
    spd = trip.spd_no.strip() or "      /SPD.LD/Setwan"
    para(doc, f"Berdasarkan Surat Perjalanan Dinas Nomor : {spd}, tanggal {tgl_id(trip.spd_tgl)}, "
              "dengan ini saya menyatakan dengan sesungguhnya bahwa:", 11, before=10, after=6)
    para(doc, "1.  Biaya uang harian, uang representasi, dan biaya hotel/penginapan dibawah ini yang tidak "
              "dapat diperoleh bukti-bukti pengeluarannya (dibayarkan secara lumpsum), meliputi :", 11, after=6)

    # Catatan: biaya transportasi TIDAK dimasukkan di dokumen ini - lihat dokumen KALKULASI.
    lines = []   # (no, uraian, hitung, jumlah)
    for g_i, g in enumerate([res.harian, res.representasi, res.hotel30]):
        for j, ln in enumerate(g):
            lines.append((str(g_i + 1) if j == 0 else "", ln.label, calc_text(ln), ln.jumlah))
    t = doc.add_table(rows=1, cols=4)
    set_borders(t)
    for c, h in zip(t.rows[0].cells, ("No", "Uraian", "Perhitungan", "Jumlah (Rp)")):
        cell_text(c, h, 10, True, "c")
    for no, ur, hit, jm in lines:
        row = t.add_row().cells
        cell_text(row[0], no, 10, align="c"); cell_text(row[1], ur, 10)
        cell_text(row[2], hit, 10); cell_text(row[3], rp(jm), 10, align="r")
    row = t.add_row().cells
    row[0].merge(row[2])
    cell_text(row[0], "Jumlah", 11, True, "c")
    cell_text(row[3], rp(res.total_dp_riil), 11, True, "r")
    widths(t, [1.1, 7.6, 5.0, 3.0])

    para(doc, "2.  Jumlah uang tersebut pada angka 1 diatas benar-benar dikeluarkan untuk pelaksanaan perjalanan "
              "dinas dimaksud dan apabila dikemudian hari terdapat kelebihan atas pembayaran, kami bersedia untuk "
              f"mengembalikan/menyetorkan kelebihan tersebut ke Kas Daerah Pemerintah Kota {st.kota.title()}.",
         11, before=10, after=6)
    para(doc, "Demikian Daftar Pengeluaran Riil ini dibuat dengan sebenarnya, untuk dipergunakan menurut perlunya.",
         11, after=10)
    para(doc, f"{st.kota.title()}, {tgl_id(trip.tgl_dokumen)}", 11, True, align="r", after=4)
    signature(doc, (["Mengetahui/Menyetujui", st.sekwan_jabatan], st.sekwan_nama, f"NIP. {st.sekwan_nip}"),
              (["Yang Melaksanakan Perjalanan Dinas,"], trip.nama.upper(), ""))


# ------------------------------------------------------------------ dokumen 2
def doc_sp(doc, trip: Trip, res: Result, st: Settings):
    para(doc, "SURAT PERNYATAAN PERTANGGUNGJAWABAN", 16, True, True, "c", after=14)
    para(doc, "Yang bertanda tangan dibawah ini :", 12, after=6)
    ident_block(doc, [("Nama", trip.nama.upper(), True), ("NIP", trip.nip or "-", False),
                      ("Jabatan", trip.jabatan_dok.upper(), True)], 12)
    para(doc, "Menyatakan bahwa saya bertanggung jawab penuh atas kebenaran Pelaksanaan Perjalanan Dinas "
              "sesuai dengan :", 12, before=10, after=6)
    total = bulatkan(res.total, st.pembulatan)
    t = doc.add_table(rows=3, cols=3)
    cell_text(t.cell(0, 0), "SPT Nomor :", 12); cell_text(t.cell(0, 1), trip.spt_no, 12)
    cell_text(t.cell(0, 2), f"Tanggal  {tgl_id(trip.spt_tgl)}", 12)
    cell_text(t.cell(1, 0), "SPD Nomor :", 12); cell_text(t.cell(1, 1), trip.spd_no, 12)
    cell_text(t.cell(1, 2), f"Tanggal  {tgl_id(trip.spd_tgl)}", 12)
    cell_text(t.cell(2, 0), "Jumlah Dana :", 12)
    t.cell(2, 1).merge(t.cell(2, 2))
    cell_text(t.cell(2, 1), f"Rp. {rp(total)},-", 12, True)
    widths(t, [3.6, 6.4, 6.4])
    para(doc, "Dokumen pertanggungjawaban perjalanan dinas disampaikan sesuai ketentuan yang berlaku untuk "
              "keperluan administrasi dan keperluan pemeriksaan aparat pengawas.", 12, before=10, after=8)
    para(doc, "Demikian surat pernyataan ini dibuat dengan sebenarnya.", 12, after=16)
    para(doc, f"{st.kota.title()}, {tgl_id(trip.tgl_dokumen)}", 12, align="r", after=0)
    para(doc, "Yang Melaksanakan Perjalanan Dinas,", 12, True, align="r", after=40)
    para(doc, trip.nama.upper(), 12, True, align="r")


# ------------------------------------------------------------------ dokumen 3
def doc_kalkulasi(doc, trip: Trip, res: Result, st: Settings):
    para(doc, "KALKULASI BIAYA PERJALANAN DINAS", 12, True, align="c", after=8)
    rows = []          # (no, sub, label, ':' , hitung, jumlah)
    n = 0

    def add(label, lns, sub=False, numbered=True):
        nonlocal n
        if numbered:
            n += 1
        if not lns:
            rows.append((str(n) if numbered else "", label, "", 0))
            return
        for j, ln in enumerate(lns):
            teks = ln.label if label is None else label
            hit = ""
            if ln.harga or ln.qty:
                hit = f"Rp {rp(ln.harga)} x {ln.qty:g}" + (f"  {ln.note}" if ln.note else "")
            rows.append((str(n) if (numbered and j == 0) else "", teks if label is None or j == 0 else "", hit, ln.jumlah))

    def pesawat(kat, numbered):
        lns = res.items.get(kat, [])
        nonlocal n
        if numbered:
            n += 1
        if not lns:
            rows.append((str(n) if numbered else "", f"- {kat}", "", 0)); return
        for j, ln in enumerate(lns):
            rows.append((str(n) if (numbered and j == 0) else "", f"- {kat}" if j == 0 else "", ln.label, ln.jumlah))

    pesawat("Tiket Pesawat Pergi", True)
    pesawat("Tiket Pesawat Pulang", False)
    add("Tiket Kapal Laut", res.items.get("Tiket Kapal Laut", []))
    add("Tiket Bus / Kereta Api", res.items.get("Tiket Bus / Kereta Api", []))
    add("Iuran Wajib / Kontribusi", res.items.get("Iuran Wajib / Kontribusi", []))
    # uang harian + representasi
    n += 1
    for j, ln in enumerate(res.harian):
        rows.append((str(n) if j == 0 else "", ln.label, f"Rp {rp(ln.harga)} x {ln.qty:g}", ln.jumlah))
    for ln in res.representasi:
        rows.append(("", ln.label, f"Rp {rp(ln.harga)} x {ln.qty:g}", ln.jumlah))
    n += 1
    hot = res.hotel30 + res.hotel_riil
    if not hot:
        rows.append((str(n), "Biaya Hotel", "", 0))
    for j, ln in enumerate(hot):
        rows.append((str(n) if j == 0 else "", ln.label.split(" (30%")[0],
                     f"Rp {rp(ln.harga)} x {ln.qty:g}  {ln.note}", ln.jumlah))
    add("Biaya Transit", res.items.get("Biaya Transit", []))
    add("Sewa Kendaraan (Mobil/Kapal/Perahu)", res.items.get("Sewa Kendaraan", []))
    n += 1
    trans = res.items.get("Biaya Transportasi", [])
    short = ["Taksi tempat kedudukan - bandara/terminal (PP)", "Taksi bandara/terminal - tempat tujuan (PP)",
             "Transportasi antar tempat tujuan"]
    tl = [(ln.label, f"Rp {rp(ln.harga)} x {ln.qty:g}", ln.jumlah) for ln in trans]
    tl += [(short[k], f"Rp {rp(l.harga)} x {l.qty:g}", l.jumlah) for k, l in enumerate(res.trans_riil) if l.qty and l.harga]
    if not tl:
        rows.append((str(n), "Biaya Transportasi", "", 0))
    for j, (lab, hit, jm) in enumerate(tl):
        rows.append((str(n) if j == 0 else "", "Biaya Transportasi" if j == 0 else "", f"{lab}  {hit}".strip(), jm))

    top = doc.add_table(rows=3, cols=3)
    for i, (a, b) in enumerate((("Nama", trip.nama.upper()), ("Tujuan", trip.tujuan_dokumen()),
                                ("Tgl / Lamanya", f"{rentang_tgl(trip.tgl_berangkat, trip.tgl_kembali)} / {trip.lama} HARI"))):
        cell_text(top.cell(i, 0), a, 11); cell_text(top.cell(i, 1), ":", 11); cell_text(top.cell(i, 2), b, 11, i == 0)
    widths(top, [3.0, 0.5, 13.5])
    set_borders(top, inner=False)

    t = doc.add_table(rows=0, cols=4)
    set_borders(t, inner=False)
    for no, lab, hit, jm in rows:
        c = t.add_row().cells
        cell_text(c[0], no, 10); cell_text(c[1], lab, 10); cell_text(c[2], hit, 10)
        cell_text(c[3], f"Rp  {rp(jm)}" if jm else "Rp  -", 10, align="r")
    total = res.total
    dib = bulatkan(total, st.pembulatan)
    for lab, val, b in (("Jumlah", total, True), ("Dibulatkan", dib, True)):
        c = t.add_row().cells
        cell_text(c[1], lab, 10, align="r"); cell_text(c[3], f"Rp  {rp(val)}", 10, b, "r")
    c = t.add_row().cells
    cell_text(c[1], f"Untuk 1 Orang Selama {trip.lama} Hari", 10)
    widths(t, [0.9, 5.4, 7.4, 3.2])

    para(doc, "", after=6)
    para(doc, f"{st.kota.title()}, {tgl_id(trip.tgl_dokumen)}", 11, align="r", after=2)
    signature(doc, (["Mengetahui", st.sekwan_jabatan + ","], st.sekwan_nama, f"NIP. {st.sekwan_nip}"),
              ([" ", st.pptk_jabatan + ","], st.pptk_nama, f"NIP. {st.pptk_nip}"), 11)


def export_docx(trip: Trip, st: Settings, path: str):
    res = hitung(trip)
    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.orientation = WD_ORIENT.PORTRAIT
    s.left_margin = s.right_margin = Cm(2)
    s.top_margin = s.bottom_margin = Cm(1.8)
    doc.styles["Normal"].font.name = FONT
    doc_dp_riil(doc, trip, res, st)
    doc.add_page_break()
    doc_sp(doc, trip, res, st)
    doc.add_page_break()
    doc_kalkulasi(doc, trip, res, st)
    doc.save(path)
    return res
