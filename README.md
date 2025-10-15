# Inference Lab

Inference Lab là bộ công cụ phục vụ học tập và mô phỏng kỹ thuật suy diễn trên cùng một cơ sở tri thức. Dự án bao gồm cả thư viện lõi, tiện ích dòng lệnh và giao diện web để thao tác với tập luật, tập sự kiện cũng như quan sát đồ thị suy diễn.

## Tính năng nổi bật

- **Quản lý tri thức linh hoạt**: thêm/sửa/xoá luật và sự kiện, nạp dữ liệu mẫu (16 luật tam giác) chỉ với vài thao tác.
- **Suy diễn tiến (Forward chaining)**:
  - Chiến lược THOA `stack` (LIFO) hoặc `queue` (FIFO).
  - Chỉ số ưu tiên luật `min` hoặc `max`.
  - Sinh đồ thị FPG và RPG minh hoạ quá trình suy diễn.
- **Suy diễn lùi (Backward chaining)**:
  - Điều chỉnh chỉ số ưu tiên mục tiêu `min` hoặc `max`.
  - Sinh đồ thị FPG thể hiện quan hệ luật–sự kiện cuối cùng.
- **Đồ thị SVG sắc nét**: xuất định dạng SVG để phóng to không bị mờ; bố cục trái→phải theo tầng, cạnh kiểu "ortho" kết hợp `concentrate=true` để giảm chồng chéo; tự động phân biệt màu giữa:
  - GT (given): vòng tròn xanh dương.
  - Fact suy ra (derived): xanh cyan nhạt.
  - KL (goal): xanh lá.
  - Rule: hình chữ nhật bo góc.
- **Trải nghiệm xem tốt**: ảnh mặc định "vừa khung" ngay khi sinh ra (không cần cuộn ngang); có các nút điều khiển `Vừa khung / − / 100% / +` và hỗ trợ `Ctrl + Wheel`.
- **Dọn dẹp tự động**: mọi ảnh đồ thị trong `inference_lab/web/static/generated/` sẽ được xoá khi tắt server web.

## Yêu cầu hệ thống

- Python ≥ 3.10
- Thư viện Python: `networkx`, `graphviz`, `flask` (tuỳ theo cách sử dụng)
- Graphviz (ứng dụng hệ thống) nếu muốn xuất ảnh FPG/RPG

Khuyến nghị tạo môi trường ảo trước khi cài đặt:

```bash
python -m venv .venv
source .venv/bin/activate            # macOS / Linux
.venv\Scripts\activate               # Windows
pip install --upgrade pip
```

## Cài đặt phụ thuộc & PATH

1. Cài package Python:

```bash
pip install -r inference_lab/requirements.txt
```

2. Cài ứng dụng Graphviz (bắt buộc để xuất FPG/RPG):

- Windows: tải installer từ `https://graphviz.org/download/` và cài đặt.
- macOS (Homebrew): `brew install graphviz`
- Ubuntu/Debian: `sudo apt-get install graphviz`

Sau khi cài, đảm bảo biến môi trường `PATH` chứa thư mục có lệnh `dot` (Windows: `dot.exe`).

<!-- CLI has been removed; project is web-only. -->

## Giao diện web

Giao diện Flask mang đến trải nghiệm trực quan:

```bash
python -m inference_lab.web
# hoặc
python -m inference_lab.web.app
```

Máy chủ mặc định lắng nghe tại `http://127.0.0.1:5000/`. Bạn có thể tinh chỉnh thông qua biến môi trường:

| Biến                | Ý nghĩa                                      | Giá trị mặc định |
| ------------------- | -------------------------------------------- | ---------------- |
| `FLASK_RUN_HOST`    | Địa chỉ bind                                 | `127.0.0.1`      |
| `FLASK_RUN_PORT`    | Cổng lắng nghe                               | `5000`           |
| `FLASK_DEBUG`       | Bật chế độ debug                             | `0`              |
| `GRAPH_MAX_HISTORY` | Số phiên đồ thị giữ lại khi server đang chạy | `12`             |

### Tính năng giao diện web

- Form nhập luật mới cho phép **dán nhiều luật cùng lúc** (tách theo xuống dòng hoặc dấu `;`).
- Chuyển đổi nhanh giữa suy diễn tiến và suy diễn lùi; giao diện sẽ hiển thị đúng nhóm tùy chọn tương ứng (THOA cho tiến, chỉ số mục tiêu cho lùi).
- Nhật ký suy diễn trực quan: bảng THOA cho forward và danh sách chứng minh cho backward.
- Ảnh FPG/RPG được sinh trong `inference_lab/web/static/generated/<session-id>/`, đồng thời được **dọn sạch khi server tắt**.

## Cấu trúc thư mục chính

```
inference_lab/
├── backward.py           # Thuật toán suy diễn lùi
├── forward.py            # Thuật toán suy diễn tiến
├── graphs.py             # Sinh đồ thị FPG/RPG bằng Graphviz
├── knowledge_base.py     # Quản lý luật và sự kiện
├── models.py             # Định nghĩa dataclass Rule
├── results.py            # Dataclass chứa kết quả suy diễn
├── sample_data.py        # Dữ liệu mẫu (tam giác)
├── utils.py              # Hàm tiện ích (parse luật, chuẩn hoá chuỗi…)
└── web/                  # Mã nguồn giao diện Flask
    ├── __init__.py       # Khởi tạo app + dọn dẹp ảnh khi tắt server
    ├── __main__.py       # Entry point `python -m inference_lab.web`
    ├── app.py            # Script tương thích (giữ nguyên cho người dùng cũ)
    ├── routes.py         # Blueprint/API `/api/infer`
    ├── static/           # Ảnh đồ thị sinh ra khi chạy
    └── templates/        # Giao diện HTML single page
```

## Đồ thị suy diễn

- **FPG (Fact Propagation Graph)**: thể hiện quan hệ luật–sự kiện; GT/Derived/KL/Rule được tô màu như mục "Tính năng nổi bật".
- **RPG (Rule Precedence Graph)**: chỉ khả dụng với suy diễn tiến.
- Định dạng xuất: SVG. Tên file mặc định theo ngữ cảnh: `forward_fpg.svg`, `forward_rpg.svg`, `backward_fpg.svg`.
- Web UI lưu file trong `inference_lab/web/static/generated/<session-id>/` và tự dọn khi tắt server.

## Kiến trúc suy diễn

- **Suy diễn tiến** dùng hàng đợi THOA:
  - `stack + min`: ưu tiên luật có ID nhỏ nhất, chọn theo LIFO.
  - `stack + max`: ưu tiên luật có ID lớn nhất, chọn theo LIFO.
  - `queue + min/max`: ưu tiên theo ID nhưng loại bỏ khác biệt bởi chiến lược FIFO.
- **Suy diễn lùi** triển khai DFS có kiểm soát vòng lặp, lần lượt thử các luật kết luận mục tiêu theo thứ tự ID tăng (`min`) hoặc giảm (`max`).
- Mọi bước trung gian được ghi lại dưới dạng `StepTrace` để hiển thị trong UI/CLI.

## Phát triển & đóng góp

1. Tạo môi trường ảo và cài đặt phụ thuộc như đã hướng dẫn.
2. Chạy web sau khi chỉnh sửa để kiểm nghiệm.
3. Nếu bạn bổ sung các luật mẫu khác, hãy cập nhật thêm trong `sample_data.py` hoặc cung cấp file riêng.
4. Dự án chưa có bộ test tự động; khuyến khích bổ sung tuỳ nhu cầu.

## Giấy phép

Dự án phục vụ học tập nội bộ; vui lòng kiểm tra lại yêu cầu bản quyền hoặc thoả thuận khi phát hành công khai.
