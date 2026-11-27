# Bản tóm tắt dự án: youtubeclaude-video-2 — "thư viện sống"

Repo và thư mục mới `youtubeclaude-video-2` (D:\youtubeclaude-video-2), tạo từ `youtubeclaude-video` kèm lịch sử git.
Repo `youtubeclaude-video` giữ nguyên, không sửa.

## Vấn đề

Mọi thứ trên hình đang bị giới hạn bởi một thư viện cố định:
- **Nhân vật:** khoảng 130 mẫu, ghép từ khoảng 14 kiểu trang phục và 25 kiểu mũ.
- **Bối cảnh:** 18 kiểu phòng, 8 kiểu phố (đều châu Âu/Nga), khoảng 45 set vẽ sẵn.
- **Phương tiện:** khoảng 40 loại vẽ bằng code.
- **Cây cỏ:** vài kiểu cây; rừng nhiệt đới là một set cố định.
- **Thời tiết:** chỉ có mưa và tuyết.

Câu chuyện ở vùng khác (Malaya, Việt Nam, Nhật, Trung Đông, châu Phi…) thiếu ngay áo quần, nhà cửa, cây cối, xe cộ, khí hậu. Model chỉ còn cách chọn món "gần nhất", nên hình sai bối cảnh và lặp lại.

## Mục tiêu

1. Dự án mới nào cũng **kiểm kê** những gì câu chuyện cần:
   - nhân vật, trang phục;
   - nhà cửa, bối cảnh;
   - phương tiện;
   - cây cỏ;
   - thời tiết;
   - đồ vật.
2. **Có sẵn thì dùng, gần giống thì sửa** (đổi màu, đổi mảnh), **chưa có thì tạo mới**.
3. Mọi món mới đều được **xem trước bằng tờ ảnh** trước khi dựng, như tờ xem trước nhân vật hiện nay.
4. Làm xong video, mọi món mới được **kiểm tra và nộp vào thư viện chung**, kèm ảnh xem trước và thẻ tìm kiếm. Lần sau dùng lại được, và repo giàu dần lên.
5. **Model yếu (Muse, Sonnet…) vẫn làm đúng** nhờ:
   - mỗi bước một lệnh;
   - phiếu điền sẵn khung;
   - ví dụ trọn vẹn;
   - công cụ tự kiểm tra, báo lỗi kèm cách sửa.

## Người dùng

- Bạn: đưa kịch bản hoặc file giọng.
- Model AI dựng video:
  - **Muse:** tạo được ảnh ngay trong lúc làm.
  - **Claude Code, Sonnet…:** không tạo ảnh, vẽ bằng code.

## Giải pháp

### 1. Thư viện sống: mỗi món là một "tài sản" có hồ sơ

```
library/
  costumes/  characters/  props/  vehicles/  buildings/  plants/  places/  plates/  weather/
    <id>/
      asset.json     hồ sơ (bên dưới)
      art.svg        hình vector (hoặc parts/ khi có bộ phận chuyển động)
      source/        ảnh gốc Muse tạo + câu lệnh đã dùng (nếu tạo từ ảnh)
      preview.png    ảnh xem trước, tự sinh
  INDEX.md           mục lục tự sinh, có ảnh, theo loại, vùng, thời kỳ
```

Hồ sơ `asset.json` ghi:
- `id`, loại, tên;
- **thẻ tìm kiếm**: vùng, thời kỳ, nhóm (ví dụ `malaya, ww2, tropical, house`);
- mô tả một dòng;
- kích thước so với một người;
- **điểm neo**: chạm đất, chỗ cầm, chỗ ngồi, tâm bánh xe, mặt bàn;
- **bộ phận chuyển động**: bánh xe quay, tán cây lay, khói bay;
- nguồn tạo: ảnh (câu lệnh, ảnh gốc) hay code;
- dự án đã tạo ra nó;
- trạng thái: nháp / đã duyệt.

Lệnh mới, mỗi lệnh một việc:

| lệnh | làm gì |
|---|---|
| `lib search "<mô tả>"` | tìm món gần nhất, kèm ảnh |
| `lib match` | đọc bảng kiểm kê của dự án; mỗi dòng trả lời: có sẵn / sửa từ món X / phải tạo mới |
| `lib new <loại> <id>` | tạo khung hồ sơ và phiếu yêu cầu cho món mới |
| `lib import <ảnh>` | ảnh → vector đúng phong cách: tách nền, gom màu, vẽ đường, ép nét viền và màu chuẩn, tìm điểm chạm đất |
| `lib preview` | tờ xem trước: món mới đứng cạnh một người, đặt trong cảnh, có lưới toạ độ |
| `lib check` | kiểm phong cách: nét viền, số màu, nền trong suốt, kích thước, điểm neo, trùng lặp |
| `lib promote` | nộp món của dự án vào thư viện chung, cập nhật mục lục |

### 2. Hai đường tạo mới, tự chọn theo model

| model | cách làm | sau đó (giống nhau) |
|---|---|---|
| **Tạo được ảnh (Muse)** | Dùng **câu lệnh mẫu** của từng loại, kèm **ảnh phong cách tham chiếu** của repo, tạo ảnh rồi lưu thẳng vào `projects/<tên>/assets/<món>/source/` | `lib import` → `lib preview` → `lib check` |
| **Không tạo được ảnh** | Tra ảnh tham khảo để tả cho đúng, rồi **vẽ bằng code**: hình khối khai báo, tham số, mảnh trang phục, theo khuôn mẫu từng loại | `lib preview` → `lib check` |

### 3. Mỗi loại một cách làm (đã chốt phương án "kết hợp")

| loại | cách làm |
|---|---|
| **Nhân vật** | Giữ bộ xương hoạt hình (đi, cử chỉ, biểu cảm). Thêm **hệ trang phục từng mảnh** gắn vào người: mũ, khăn, áo, quần, áo khoác, giày, phụ kiện, quân hàm. Mảnh tự cử động theo người. Ảnh tham khảo hoặc ảnh Muse dùng để lấy bảng màu và hình dáng mảnh. Mảnh nào chưa có thì vẽ mới theo khuôn (nón lá, songkok, sarong, khăn turban Sikh, mũ rộng vành của Úc…). |
| **Phương tiện** | Ảnh → vector, **tách bộ phận**: thân, bánh, xích, tháp pháo, cánh quạt. Bánh quay, pháo giật, xe nảy. Xe đạp kèm **tư thế đạp xe** cho nhân vật. |
| **Nhà cửa, công trình** | Ảnh → vector. Ghép được vào bộ lắp phố và làng: nhà phố người Hoa có hành lang 5 bước chân, nhà sàn Mã Lai, đền, chùa, nhà thờ Hồi giáo… |
| **Cây cỏ** | Ảnh → vector, **tán và thân tách riêng** để lay theo gió. Có thể trồng thành hàng (đồn điền cao su, dừa), thành khóm (tre), thành rừng (bìa rừng nhiều lớp). |
| **Đồ vật** | Như hiện nay: hình khối khai báo hoặc ảnh → vector, có điểm cầm. |
| **Phông nền xa** | **Được dùng thẳng ảnh vẽ**, chia lớp trời / xa / giữa để máy quay có chiều sâu. Nhân vật, xe, cây gần đều là vector đứng lên trên. |
| **Thời tiết** | **Hệ thời tiết có tham số**, không cần ảnh: mưa (nhẹ đến mưa nhiệt đới), tuyết, sương mù, hơi ẩm, nắng gắt, bão cát, bụi, khói, tro, sấm chớp, lá và hoa rơi; cường độ, hướng gió, lớp trước/sau nhân vật. |

### 4. Quy trình mỗi dự án

```
1. Chuẩn bị       (như hiện nay)
2. Hiểu kịch bản  (như hiện nay) + BẢNG KIỂM KÊ: mọi nhân vật, trang phục, nơi chốn, nhà, xe, cây, thời tiết, đồ vật
3. Đối chiếu      lib match → có sẵn / sửa / tạo mới
4. Tạo mới        mỗi món theo trang hướng dẫn của loại đó (đường ảnh hoặc đường code)
5. Xem trước      tờ ảnh cho từng loại → sửa đến khi đạt
6. Dựng video     thẻ cảnh dùng món mới như món có sẵn
7. Nộp thư viện   lib check + lib promote → món mới vào thư viện chung, mục lục cập nhật
```

### 5. Cho model yếu

- Mỗi loại một trang hướng dẫn, gồm:
  - khi nào dùng;
  - phiếu điền;
  - **câu lệnh tạo ảnh mẫu**;
  - cách vẽ bằng code;
  - **một ví dụ trọn vẹn từ đầu đến cuối**;
  - lỗi hay gặp.
- **Ảnh phong cách tham chiếu**, tự sinh từ engine, để Muse tạo ảnh đúng nét.
- **Tờ xem trước có lưới toạ độ**, để đọc được vị trí khi điền điểm neo.
- Công cụ kiểm tra báo lỗi bằng câu chỉ dẫn: sai gì, sửa thế nào.
- Bảng quyết định một trang: "cần X → tìm → có / sửa / tạo theo cách nào".

## Video thử (chứng minh cả quy trình)

- **Nguồn:** dự án `fall-of-singapore`, đoạn **09:36–10:42** (khoảng 66 giây).
- **Nội dung:**
  - Quân Nhật lấy xe đạp từ cửa hàng và dân thường, đạp xuống phía nam từng nhóm 40–50 người, cười nói như đi xem bóng đá; một sĩ quan Anh nằm nấp ven đường nhìn họ đi qua.
  - Huyền thoại "rừng rậm": phần lớn thực ra là đồn điền cao su, rừng dừa, làng mạc và đường sá; rừng thật chỉ ở rìa.
  - Quân Nhật đi theo đường và lối mòn trong đồn điền, vòng qua phòng tuyến Anh, nhanh hơn tốc độ bên kia đào công sự.
- **Món mới dự kiến:**
  - xe đạp và tư thế đạp xe; đoàn người đạp xe;
  - trang phục dân Mã Lai và người Hoa; lính Ấn đội khăn Sikh; mũ rộng vành của lính Úc;
  - nhà phố người Hoa có cửa hàng xe đạp; nhà sàn kampong;
  - cây cao su có chén hứng mủ, trồng thành hàng; dừa; bìa rừng rậm;
  - đường đất đỏ;
  - tư thế nằm nấp quan sát; tư thế đào đất và cái xẻng;
  - hơi ẩm và nắng nhiệt đới;
  - phông nền xa: đồi rừng nhiệt đới.
- **Đạt khi:**
  1. Mọi món mới đi trọn quy trình (tạo → xem trước → kiểm tra → nộp thư viện), có ảnh trong mục lục.
  2. Video 1 phút đúng nội dung từng câu, không lẫn bối cảnh châu Âu.
  3. Món tạo từ ảnh đứng cạnh nhân vật engine không bị lệch nét.
  4. Có hướng dẫn và ví dụ đủ để model yếu làm lại được.

## Các giai đoạn

1. **Nền móng thư viện:** hồ sơ tài sản, `lib search / match / new / preview / check / promote`, mục lục; lập hồ sơ cho mọi thứ đang có (nhân vật mẫu, đồ vật, xe, bộ lắp, hình vẽ).
2. **Ảnh → vector:** `lib import`; engine hiển thị tài sản vector có bộ phận chuyển động và đổi màu; ảnh phong cách tham chiếu; câu lệnh mẫu.
3. **Trang phục từng mảnh** cho nhân vật; tư thế mới (đạp xe, nằm nấp, đào đất).
4. **Thời tiết có tham số; cây cỏ trồng hàng hoặc khóm; phông nền nhiều lớp.**
5. **Video thử Malaya 1 phút.** Món mới tạo bằng cả hai đường: Muse tạo ảnh (bạn chạy), hoặc mình vẽ bằng code nếu chưa có ảnh. Nộp thư viện.
6. **Tài liệu cho model yếu:** từng loại, ví dụ trọn vẹn, cập nhật skill, AGENTS, playbook, CHANGELOG.

Sau mỗi giai đoạn: kiểm tra và tờ ảnh để bạn xem; xong cả 6 giai đoạn mới đưa lên GitHub, như cách làm trước giờ.

## Không làm trong đợt này

- Không để engine tự gọi dịch vụ tạo ảnh qua khoá API (đã chốt: Muse tạo ảnh trong lúc làm).
- Không vẽ thẳng nhân vật từ ảnh (nhân vật vẽ từ ảnh không cử động được); nhân vật luôn dùng bộ xương với trang phục từng mảnh.
- Không làm hết mọi vùng. Đợt này làm bộ Malaya / Đông Nam Á 1942; vùng khác lớn dần theo từng dự án.
- Không sửa `youtubeclaude-video` và các repo khác.
- Không đăng gì lên YouTube.

## Rủi ro và cách xử lý

| rủi ro | cách xử lý |
|---|---|
| Ảnh AI lệch phong cách | câu lệnh mẫu + ảnh phong cách tham chiếu + bước ép nét viền và bảng màu sau khi chuyển vector + `lib check` |
| Vector từ ảnh quá rối (nhiều mảnh nhỏ) | giới hạn số màu, gộp mảnh nhỏ, làm mượt; vượt ngưỡng thì báo lỗi và đề nghị tạo lại ảnh đơn giản hơn |
| Model yếu điền sai điểm neo | tờ xem trước có lưới toạ độ; công cụ tự tìm điểm chạm đất và tâm bánh xe; kiểm tra tự động |
| Trùng món trong thư viện | `lib promote` kiểm tên, thẻ và độ giống ảnh; nếu trùng thì gộp làm biến thể |
| Ổ D: còn khoảng 21 GB (đầy 98%) | chỉ giữ ảnh gốc đã thu nhỏ; ảnh gốc to để ngoài git; nên dọn bớt bản render cũ |
| Bản quyền ảnh | không đồ lại ảnh chụp có bản quyền; ảnh tham khảo chỉ dùng để tả; ảnh tạo mới do Muse vẽ theo phong cách repo |
