# Cấu trúc tuyên bố, khai TRƯỚC khi chạy thí nghiệm

Bài tạp chí, chủ đề thuộc trụ 2 + trụ 4 của session QAI-SAGIN mà Hảo đồng chủ trì.
Ngày khai: 05/09/2026. ⛔ Chưa chạy thí nghiệm nào tại thời điểm khai.

CLAIM: Trong văn liệu semantic communication cho mạng phi mặt đất, một tỉ lệ lớn các công trình
được chính lĩnh vực này trích dẫn là "giải quyết" một hạn chế đặc thù NTN (trễ lan truyền lớn,
Doppler hàng trăm kHz, cửa sổ nhìn thấy ngắn, suy hao biến thiên theo góc ngẩng) lại được đánh
giá trong điều kiện KHÔNG hiện thực hoá chính hạn chế đó, và khi đánh giá lại dưới điều kiện
tuân thủ 3GPP TR 38.821 thì mức lợi ích công bố suy giảm đáng kể.

MEASUREMENT: Ba phép đo tách rời. (1) KIỂM KÊ: lấy quần thể là các công trình được liệt kê ở
Bảng II, III, IV của khảo sát arXiv:2606.05216, mã hoá từng cặp (hạn chế NTN, công trình được
trích là giải quyết hạn chế đó) theo một danh mục hiệu ứng vật lý neo vào TR 38.821, hai người
mã hoá độc lập, báo Cohen kappa. (2) ĐỘ LỚN: từ TLE Starlink công khai và SGP4, đo phân bố thật
của Doppler, trễ, tốc độ biến thiên SNR trong một lượt bay, và độ dài cửa sổ nhìn thấy, để nói
hiệu ứng bị bỏ qua LỚN cỡ nào chứ không chỉ nói nó vắng mặt. (3) ĐÁNH GIÁ LẠI: huấn luyện lại
mô hình semantic đại diện trên GPU của VPS, đo dưới kênh AWGN cố định như bài gốc dùng, rồi đo
lại dưới vệt kênh sinh từ quỹ đạo thật, báo chênh lệch.

IF NULL: Nếu kiểm kê cho thấy PHẦN LỚN công trình đã hiện thực hoá đúng hạn chế mà chúng được
trích dẫn, và đánh giá lại cho thấy mức lợi ích GIỮ NGUYÊN dưới kênh thật, thì bài vẫn còn ba
thứ. Thứ nhất, một danh mục kiểm hiện thực NTN neo vào chuẩn 3GPP chứ không do tác giả tự nghĩ,
cùng quy trình mã hoá và hệ số đồng thuận, dùng lại được cho khảo sát sau. Thứ hai, phép đo độ
lớn từ quỹ đạo thật là số liệu độc lập có giá trị riêng: nó nói cho người thiết kế biết Doppler
và biến thiên SNR thực tế nằm ở dải nào, bất kể văn liệu có mô phỏng chúng hay không. Thứ ba,
bộ sinh kênh tuân thủ 38.821 và bộ khung đánh giá lại được phát hành, biến kết quả null thành
một XÁC NHẬN DƯƠNG rằng thực hành đánh giá của lĩnh vực này lành mạnh, kèm công cụ để giữ nó
lành mạnh. Kết quả null ở đây đổi GIỌNG của bài, không đổi số đóng góp.

SURVIVES: yes

CONTRIBUTIONS:
  - [independent] Danh mục kiểm hiện thực kênh NTN neo vào 3GPP TR 38.821 và bảy hạn chế do
    chính khảo sát của lĩnh vực nêu ra, kèm quy trình mã hoá hai người và hệ số đồng thuận.
    Đúng bất kể kiểm kê ra tỉ lệ nào.
  - [independent] Phân bố đo được của Doppler, trễ, tốc độ biến thiên SNR và độ dài cửa sổ nhìn
    thấy, tính từ TLE công khai bằng SGP4. Đây là số về VẬT LÝ, không phải về văn liệu, nên
    không phụ thuộc kết quả kiểm kê.
  - [independent] Bộ sinh kênh NTN tuân thủ 38.821 cắm được vào bộ khung semantic communication
    hiện có, phát hành kèm bài. Giá trị của nó không phụ thuộc chiều của kết quả.
  - [dependent] Kết luận rằng mức lợi ích công bố của semantic communication cho NTN bị thổi
    phồng do điều kiện đánh giá. Chỉ đúng nếu phép đo (3) cho thấy suy giảm.

## Ghi chú ràng buộc, phải giữ khi viết

- ⛔ KHÔNG được nói lĩnh vực này "cẩu thả". Bảng III và IV của khảo sát CÓ cột "Channel/protocol
  consideration", tức lĩnh vực có ý thức về chuyện này. Tuyên bố phải hẹp: cột đó GHI NHẬN chứ
  không ĐỐI CHIẾU, và không ai đếm.
- ⛔ Khe "chỉ số đánh giá semantic communication" ĐÃ BỊ CHIẾM bởi arXiv:2608.21626 (Ericsson,
  21/08/2026). Bài này KHÔNG được đề xuất chỉ số mới. Nó chỉ hỏi về ĐIỀU KIỆN đánh giá.
- ⛔ Khe "baseline cổ điển yếu trong DeepJSCC" ĐÃ KÍN: văn liệu đã tự công bố ca BPG+LDPC thắng
  DeepJSCC về PSNR trên ảnh phân giải cao. KHÔNG được bán lại luận điểm đó.
- ⚠ Không đụng bài nhà: Hảo chưa có bài nào về semantic communication. Đây là hướng đầu tiên
  trong bảy lần occupied-check gần đây hoàn toàn sạch cả với bài người khác lẫn bài của chính
  mình ở TRỤ này.
- ⚠ Phải khai giới hạn: một khảo sát là MỘT khung lấy mẫu. Nếu quần thể chỉ lấy từ 2606.05216
  thì đó là mẫu tiện lợi, phải nói rõ và nên bổ sung một nguồn thứ hai độc lập.

---

## ⛔ 05/09/2026, NGAY SAU E1: MOT CO CHE DA GIA DINH BI BAC, ghi lai truoc khi viet

Truoc khi chay, toi gia dinh co che la: *"bai mo phong o SNR co dinh, nhung SNR that troi manh
trong lue truyen mot tam anh, nen gia dinh SNR tinh bi vo"*.

**E1 BAC gia dinh nay.** Toc do bien thien FSPL trung vi la **0,05 dB/s**. Trong 1 giay truyen,
SNR dich **0,05 dB**; trong 10 giay cung chi **0,48 dB**. Tuc gia dinh SNR gan nhu tinh trong
mot khoi truyen la **DUNG**, va phat hien nay **benh vuc** van lieu chu khong buoc toi.

⇒ **KHONG duoc viet co che nay vao bai.** Phai bao ra ket qua nay nhu mot ket qua, vi no la cau
tra loi cho mot cau hoi hop ly ma nguoi doc se tu hoi.

**Co che CON SONG, do duoc o E1:**

1. **Doppler.** Dinh **359 kHz** trung vi o Ka-band 20 GHz (cuc dai 433 kHz), **35,9 kHz** o
   S-band. Toc do troi toi **10,1 kHz/s**. De so sanh, khoang cach song mang con cua 5G NR la
   15-120 kHz, tuc do lech Doppler o Ka bang 3 den 24 song mang con.
2. **Lech SNR giua HUAN LUYEN va TRIEN KHAI.** Bien thien FSPL tron mot luot bay la **3,74 dB**
   trung vi, cuc dai **6,48 dB**. Mo hinh semantic thuong huan luyen tai MOT muc SNR. Cau hoi
   dung khong phai "SNR co troi trong luc truyen khong" (khong) ma **"mo hinh huan luyen o mot
   diem SNR con dung o dau kia cua luot bay khong"**.
3. **Cua so nhin thay huu han**: trung vi **205 s** o goc ngang 25 do.

⇒ Phep do (3) trong MEASUREMENT phai doi lai cho dung: khong phai "danh gia duoi vet SNR troi
trong khoi truyen", ma **danh gia mo hinh huan luyen tai mot SNR tren TOAN DAI SNR cua luot bay,
va duoi do lech Doppler du**.
