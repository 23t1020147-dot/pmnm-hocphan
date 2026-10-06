import csv
import io
import unicodedata

from flask import (
    Flask,
    render_template_string,
    request,
    jsonify,
    abort,
    redirect,
    url_for,
    Response,
    make_response
)

app = Flask(__name__)


# ============================================================
# DỮ LIỆU SINH VIÊN
# ============================================================

STUDENTS = {
    "23T1020001": {
        "name": "Nguyễn Văn An",
        "Lop": "K47A",
        "scores": {
            "PMMNM": 8.5,
            "CSDL": 7.0,
            "MMT": 9.01
        }
    },

    "23T1020002": {
        "name": "Trần Thị Bình",
        "Lop": "K47A",
        "scores": {
            "PMMNM": 6.0,
            "CSDL": 5.5,
            "MMT": 7.0
        }
    },

    "23T1020003": {
        "name": "Lê Hoàng Cường",
        "Lop": "K47B",
        "scores": {
            "PMMNM": 9.5,
            "CSDL": 9.0
        }
    },

    "23T1020004": {
        "name": "Phạm Minh Dũng",
        "Lop": "K47B",
        "scores": {
            "PMMNM": 4.0,
            "CSDL": 3.5,
            "MMT": 5.0
        }
    },

    "23T1020005": {
        "name": "Hoàng Thu Hà",
        "Lop": "K47A",
        "scores": {}
    },

    "23T1020006": {
        "name": "VO Quoc Khinh",
        "Lop": "K47C",
        "scores": {
            "PMMNM": 7.5,
            "MMT": 8.0
        }
    }
}


# ============================================================
# GIAO DIỆN TRANG CHỦ
# ============================================================

INDEX_HTML = """
<h1>Trang chủ</h1>

<p>Tổng số sinh viên: {{ so_sv }}</p>
<p>Số lớp: {{ so_lop }}</p>

<a href="{{ url_for('student_list') }}">
    Xem danh sách sinh viên
</a>
<br>

<a href="{{ url_for('search') }}">
    Tìm kiếm sinh viên
</a>
<br>

<a href="{{ url_for('api_students') }}">
    Xem API
</a>
"""


# ============================================================
# GIAO DIỆN DANH SÁCH SINH VIÊN
# ============================================================

STUDENTS_HTML = """
<h1>
    Danh sách sinh viên

    <!-- Icon tải xuống CSV -->
    <a
        href="{{ url_for('download_students', lop=lop_dang_loc, q=q or None) }}"
        title="Tải xuống CSV"
        style="text-decoration:none; font-size:0.7em;"
    >
        &#11015;&#65039;
    </a>
</h1>


<!-- Lọc theo lớp -->

<a href="{{ url_for('student_list', q=q or None) }}">
    Tất cả
</a>

{% for lop in ds_lop %}
    |
    <a href="{{ url_for('student_list', lop=lop, q=q or None) }}">
        {{ lop }}
    </a>
{% endfor %}


<!-- Ô tìm kiếm -->

<form
    method="get"
    action="{{ url_for('student_list') }}"
    style="margin-top:10px;"
>

    {% if lop_dang_loc %}
        <input
            type="hidden"
            name="lop"
            value="{{ lop_dang_loc }}"
        >
    {% endif %}

    <input
        type="text"
        name="q"
        value="{{ q }}"
        placeholder="Tìm theo MSSV hoặc họ tên..."
    >

    <button type="submit">
        Tìm
    </button>

    {% if q %}
        <a href="{{ url_for('student_list', lop=lop_dang_loc or None) }}">
            Xóa tìm kiếm
        </a>
    {% endif %}

</form>


<br>
<br>


{% if ds %}

<table border="1" cellpadding="6">

    <tr>
        <th>MSSV</th>
        <th>Họ tên</th>
        <th>Lớp</th>
        <th>Điểm TB</th>
        <th>Xếp loại</th>
        <th>Tải xuống</th>
    </tr>


    {% for sv in ds %}

    <tr>

        <td>
            <a href="{{ url_for('student_detail', mssv=sv.mssv) }}">
                {{ sv.mssv }}
            </a>
        </td>

        <td>
            {{ sv.name }}
        </td>

        <td>
            {{ sv.lop }}
        </td>

        <td>
            {{ sv.sodiem if sv.sodiem is not none else '-' }}
        </td>

        <td>
            {{ sv.xep_loai or '-' }}
        </td>

        <td style="text-align:center;">

            <a
                href="{{ url_for('export_scores', mssv=sv.mssv) }}"
                title="Tải bảng điểm CSV"
                style="text-decoration:none;"
            >
                &#11015;&#65039;
            </a>

        </td>

    </tr>

    {% endfor %}

</table>

{% else %}

<p>
    Không có sinh viên phù hợp.
</p>

{% endif %}
"""


# ============================================================
# GIAO DIỆN CHI TIẾT SINH VIÊN
# ============================================================

DETAIL_HTML = """
<h1>{{ sv.name }}</h1>

<p>
    MSSV: {{ mssv }}
</p>

<p>
    Lớp:
    <a href="{{ url_for('student_list', lop=sv.Lop) }}">
        {{ sv.Lop }}
    </a>
</p>

<p>
    Điểm TB:
    {{ sodiem if sodiem is not none else '-' }}
</p>

<p>
    Xếp loại:
    {{ xep_loai or '-' }}
</p>


<h3>
    Bảng điểm
</h3>


{% if sv.scores %}

<table border="1" cellpadding="6">

    <tr>
        <th>Học phần</th>
        <th>Điểm</th>
    </tr>


    {% for hp, d in sv.scores.items() %}

    <tr>
        <td>
            {{ hp }}
        </td>

        <td>
            {{ d }}
        </td>
    </tr>

    {% endfor %}

</table>

{% else %}

<p>
    Chưa có điểm.
</p>

{% endif %}


<p>
    <a href="{{ url_for('export_scores', mssv=mssv) }}">
        Tải bảng điểm (CSV)
    </a>
</p>


<p>
    Link rút gọn:

    <a href="{{ url_for('short_link', mssv=mssv) }}">
        {{ url_for('short_link', mssv=mssv, _external=True) }}
    </a>
</p>


<br>

<a href="{{ url_for('student_list') }}">
    &larr; Quay lại danh sách
</a>
"""


# ============================================================
# GIAO DIỆN CÂU 6 - TÌM KIẾM AN TOÀN
# ============================================================

SEARCH_HTML = """
<h1>
    Tìm kiếm sinh viên
</h1>


<form
    method="get"
    action="{{ url_for('search') }}"
>

    <input
        type="text"
        name="q"
        value="{{ q }}"
        placeholder="Nhập MSSV hoặc họ tên..."
    >

    <button type="submit">
        Tìm kiếm
    </button>

</form>


{% if q %}

<p>
    Tìm thấy
    <strong>{{ ds|length }}</strong>
    kết quả cho
    "<strong>{{ q }}</strong>"
</p>

{% endif %}


{% if ds %}

<ul>

    {% for sv in ds %}

    <li>

        <a href="{{ url_for('student_detail', mssv=sv.mssv) }}">
            {{ sv.name }}
        </a>

        -
        {{ sv.mssv }}

        -
        {{ sv.lop }}

    </li>

    {% endfor %}

</ul>


{% elif q %}

<p>
    Không tìm thấy sinh viên phù hợp.
</p>

{% endif %}


<br>

<a href="{{ url_for('student_list') }}">
    &larr; Quay lại danh sách sinh viên
</a>
"""


# ============================================================
# HÀM TÍNH ĐIỂM TRUNG BÌNH
# ============================================================

def tinh_sodiem_tb(scores):

    if len(scores) == 0:
        return None

    return round(
        sum(scores.values()) / len(scores),
        2
    )


# ============================================================
# HÀM XẾP LOẠI
# ============================================================

def xep_loai(sodiem):

    if sodiem is None:
        return None

    if sodiem >= 8:
        return "Giỏi"

    elif sodiem >= 6.5:
        return "Khá"

    elif sodiem >= 5:
        return "Trung bình"

    else:
        return "Yếu"


# ============================================================
# BỎ DẤU TIẾNG VIỆT
# ============================================================

def bo_dau(text):

    text = text.replace("đ", "d").replace("Đ", "D")

    text = unicodedata.normalize(
        "NFD",
        text
    )

    return "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    ).lower()


# ============================================================
# LẤY DANH SÁCH SINH VIÊN
# Dùng cho:
# - Danh sách sinh viên
# - Lọc lớp
# - Tìm kiếm
# - Câu 6
# ============================================================

def lay_ds(lop, q=""):

    q = bo_dau(q.strip())

    ds = []

    for mssv, sv in STUDENTS.items():

        # Lọc theo lớp
        if lop != "" and sv["Lop"] != lop:
            continue

        # Tìm kiếm theo MSSV hoặc họ tên
        if (
            q
            and q not in bo_dau(mssv)
            and q not in bo_dau(sv["name"])
        ):
            continue

        sodiem = tinh_sodiem_tb(
            sv["scores"]
        )

        ds.append({
            "mssv": mssv,
            "name": sv["name"],
            "lop": sv["Lop"],
            "sodiem": sodiem,
            "xep_loai": xep_loai(sodiem)
        })

    return ds


# ============================================================
# CÂU 1 - TRANG CHỦ
# ============================================================

@app.route("/")
def index():

    so_sv = len(STUDENTS)

    ds_lop = set(
        sv["Lop"]
        for sv in STUDENTS.values()
    )

    return render_template_string(
        INDEX_HTML,
        so_sv=so_sv,
        so_lop=len(ds_lop)
    )


# ============================================================
# CÂU 2 - DANH SÁCH SINH VIÊN
# ============================================================

@app.route("/students")
def student_list():

    lop = request.args.get(
        "lop",
        ""
    ).upper()

    q = request.args.get(
        "q",
        ""
    ).strip()

    ds = lay_ds(
        lop,
        q
    )

    ds_lop = sorted(
        set(
            sv["Lop"]
            for sv in STUDENTS.values()
        )
    )

    return render_template_string(
        STUDENTS_HTML,
        ds=ds,
        ds_lop=ds_lop,
        lop_dang_loc=lop,
        q=q
    )


# ============================================================
# CÂU 2 - TẢI DANH SÁCH SINH VIÊN CSV
# ============================================================

@app.route("/students.csv")
def download_students():

    lop = request.args.get(
        "lop",
        ""
    ).upper()

    q = request.args.get(
        "q",
        ""
    ).strip()

    ds = lay_ds(
        lop,
        q
    )

    f = io.StringIO()

    w = csv.writer(f)

    w.writerow([
        "MSSV",
        "Họ tên",
        "Lớp",
        "Điểm TB",
        "Xếp loại"
    ])

    for sv in ds:

        w.writerow([
            sv["mssv"],
            sv["name"],
            sv["lop"],
            (
                sv["sodiem"]
                if sv["sodiem"] is not None
                else "-"
            ),
            sv["xep_loai"] or "-"
        ])

    # utf-8-sig giúp Excel đọc tiếng Việt
    data = f.getvalue().encode(
        "utf-8-sig"
    )

    return Response(
        data,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=students.csv"
        }
    )


# ============================================================
# API TRẢ VỀ JSON
# ============================================================

@app.route("/api/students")
def api_students():

    return jsonify(
        STUDENTS
    )


# ============================================================
# CÂU 3 - CHI TIẾT SINH VIÊN
# ============================================================

@app.route("/students/<mssv>")
def student_detail(mssv):

    sv = STUDENTS.get(
        mssv
    )

    if sv is None:

        abort(
            404,
            description=
            f"Không có sinh viên với MSSV = {mssv}."
        )

    sodiem = tinh_sodiem_tb(
        sv["scores"]
    )

    return render_template_string(
        DETAIL_HTML,
        mssv=mssv,
        sv=sv,
        sodiem=sodiem,
        xep_loai=xep_loai(sodiem)
    )


# ============================================================
# CÂU 5 - XUẤT BẢNG ĐIỂM CSV
# ============================================================

@app.route("/students/<mssv>/export")
def export_scores(mssv):

    sv = STUDENTS.get(
        mssv
    )

    if sv is None:

        abort(
            404,
            description=
            f"Không có sinh viên với MSSV = {mssv}."
        )

    noi_dung = "hoc_phan,diem\n"

    for hp, d in sv["scores"].items():

        noi_dung += f"{hp},{d}\n"

    resp = make_response(
        noi_dung
    )

    resp.headers[
        "Content-Type"
    ] = "text/csv; charset=utf-8"

    resp.headers[
        "Content-Disposition"
    ] = (
        f"attachment; "
        f"filename=diem_{mssv}.csv"
    )

    return resp


# ============================================================
# CÂU 4 - LINK RÚT GỌN
# /sv/<mssv>
# -> /students/<mssv>
# ============================================================

@app.route("/sv/<mssv>")
def short_link(mssv):

    return redirect(
        url_for(
            "student_detail",
            mssv=mssv
        ),
        code=301
    )


# ============================================================
# CÂU 6 - TÌM KIẾM AN TOÀN
# ============================================================

@app.route("/search")
def search():

    # Lấy từ khóa từ URL
    q = request.args.get(
        "q",
        ""
    ).strip()

    # Tìm theo MSSV hoặc họ tên
    ds = lay_ds(
        "",
        q
    )

    return render_template_string(
        SEARCH_HTML,
        q=q,
        ds=ds
    )


# ============================================================
# CHẠY SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=8000
    )