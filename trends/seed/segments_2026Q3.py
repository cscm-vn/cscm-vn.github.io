import json
S=lambda n,u,d:dict(name=n,url=u,date=d)
QD425=S("Bộ Xây dựng – QĐ 425/QĐ-BXD (suất vốn 2025, ban hành 30/03/2026)","https://luatvietnam.vn/dau-tu/quyet-dinh-425-qd-bxd-2026-cong-bo-suat-von-dau-tu-va-gia-xay-dung-tong-hop-2025-430428-d1.html","2026-03-30")
SAV_HN=S("Savills HN Q3/2026 (VietnamBiz)","https://vietnambiz.vn/savills-luong-can-ho-ban-duoc-trong-quy-iii2026-giam-48-dong-can-ho-2-4-ty-dong-gan-nhu-bien-mat-20261015154858608.htm","2026-10-15")
CBRE_HN=S("CBRE HN Q3/2026 (CVS News)","https://news.cvs.vn/thi-truong-can-ho-ha-noi-ben-ban-tri-hoan-cho-thi-61933","2026-10-08")
CBRE_HCM=S("CBRE TP.HCM Q3/2026 (VietnamBiz)","https://vietnambiz.vn/thi-truong-can-ho-tp-hcm-chung-lai-gia-thu-cap-giam-tren-10-tai-mot-so-du-an-2026101514220560.htm","2026-10-15")
DKRA=S("DKRA Q3/2026 (Báo Đầu tư)","https://baodautu.vn/thi-truong-chung-cu-phia-nam-quy-iii2026-chao-ban-13215-can-ho-tieu-thu-chi-3471-can-d721173.html","2026-10-10")
DKRA_PDF=S("DKRA – báo cáo TP.HCM & vùng phụ cận Q3/2026 (PDF)","https://www.dkra.vn/pdf/dkra-consultingbao-cao-thi-tru%CC%9Bo%CC%9Bng-ba%CC%82t-do%CC%82ng-san-nha-o%CC%9B-tp-hcm--vung-phu-ca%CC%82n-q32026_vi_1791799294.pdf","2026-10-10")
VILLA=S("CBRE thấp tầng Q3/2026 (CafeF)","https://cafef.vn/biet-thu-lien-ke-ha-noi-tang-gia-so-cap-33-trong-1-nam-thi-truong-tphcm-dien-bien-trai-chieu-188261017084427692.chn","2026-10-17")
VILLA2=S("VnExpress – Chỉ 30% biệt thự liền kề sơ cấp có người mua","https://vnexpress.net/chi-30-biet-thu-lien-ke-so-cap-co-nguoi-mua-5133703.html","2026-10-17")
NAI=S("NAI Vietnam – báo cáo Q3/2026 (PDF)","https://naivietnam.com/wp-content/uploads/2026/10/VN_Q32026_NAI_Vietnam_Quarterly_Report.pdf","2026-10-15")
NAI2=S("NAI Vietnam – Market Snapshot Q3/2026","https://naivietnam.com/vi/market-snapshot-q3-2026/","2026-10-15")
COND=S("VnExpress – condotel Q3/2026 (DKRA)","https://vnexpress.net/luong-tieu-thu-condotel-quy-iii-tang-hon-5-lan-5132771.html","2026-10-14")
NOXH=S("Bộ Xây dựng – NOXH 9T/2026 (Dân trí)","https://dantri.com.vn/bat-dong-san/bo-xay-dung-thong-tin-tien-do-hon-910000-can-nha-o-xa-hoi-tren-ca-nuoc-20261015154236153.htm","2026-10-15")
NOXH2=S("VietnamPlus – 46.500 căn NOXH 9 tháng","https://en.vietnamplus.vn/vietnam-completes-nearly-46500-social-rental-homes-in-9-months-post353765.vnp","2026-10-15")
VARS=S("VARS – báo cáo thị trường Q3/2026","https://varsvietnam.vn/nghien-cuu-thi-truong/bao-cao-thi-truong-bat-dong-san-viet-nam-quy-iii-2026-73","2026-10-16")
KF=S("Knight Frank VN Q3/2026 (PDF)","https://www.knightfrank.com.vn/site-assets/research/kfvn-q3-2026-market-report_vn---with-econ.pdf","2026-10-15")
VNE_KT=S("VnExpress – giảm giá kỹ thuật chung cư mới","https://vnexpress.net/song-ngam-giam-gia-chung-cu-moi-5133944.html","2026-10-18")
NOBLE=S("Stockbiz – Tây Hồ Tây 200–300 tr/m²","https://stockbiz.vn/tin-tuc/chung-cu-ha-noi-thiet-lap-mat-bang-gia-moi-mot-du-an-chung-cu-hang-hieu-khu-tay-ho-tay-cham-nguong-200-300-trieum2/33870138","2026-10-01")
GM=S("Chuyển động Thị trường – Novaland","https://www.chuyendongthitruong.vn/chuyen-dong-moi-cua-novaland-332450.html","2026-07-30")
PRIVE=S("The Privé – vật liệu bàn giao","https://canhotheprive.com.vn/danh-muc-vat-lieu-ban-giao/","2026-10-01")
CITYON=S("The CityOn – MIK","https://cityon.com.vn/","2026-10-05")
def R(**k): return k
segs=[
dict(id="hang-sang",name="Hạng sang / siêu sang",def_="Căn hộ giá sơ cấp ≳120 triệu đ/m² thông thủy (hàng hiệu, vị trí lõi).",
 hn=R(price="114–330 triệu đ/m² (chào bán 10/2026; Noble Crystal Tây Hồ 188–330, Lumière Essence Peak 175–185, Seasons Garden 145–190, BRG Diamond thứ cấp 114–152)",trend="↑ n/n — mặt bằng mới khu Tây Hồ Tây chạm 200–300 triệu đ/m²; một số dự án mới thử 'giảm giá kỹ thuật' (Ciputra từ 95 triệu đ/m²)",supply="Không có số liệu riêng phân khúc; toàn thị trường căn hộ HN Q3: ~6.200 căn mở bán (CBRE), 3.100 căn (Savills)",absorption="Savills: >70% căn bán được có giá >6 tỷ đồng; hấp thụ toàn thị trường 39%",inventory="n/a (không công bố riêng)",projects="Noble Crystal/Noble West Lake (Sun Group), Lumière Essence Peak & Seasons Garden (Masterise), BRG Diamond Residence (BRG)",sources=[NOBLE,SAV_HN,VNE_KT]),
 hcm=R(price="~210–230 triệu đ/m² (The Grand Manhattan chuyển nhượng, chưa VAT); Eaton Park 1PN từ 6,2 tỷ đồng",trend="→ giá sơ cấp toàn thị trường −2,3% q/q (CBRE); phân khúc hàng hiệu giữ giá",supply="Không có số liệu riêng; toàn thị trường 3.267 căn mở bán Q3 (−53% n/n, CBRE)",absorption="45% nguồn cung mới (CBRE, toàn thị trường)",inventory="n/a",projects="The Grand Manhattan (Novaland, GC Ricons), Eaton Park (Gamuda Land), The OpusK – The Metropole Thủ Thiêm (MEP Hawee), Grand Marina (Masterise)",sources=[GM,CBRE_HCM]),
 spec="Thiết bị nhập khẩu thương hiệu châu Âu/Nhật (Kohler/Grohe/Duravit, bếp Gaggenau/Miele/Bosch, phụ kiện Hafele/Blum), mặt dựng kính hộp Low-E, sàn gỗ kỹ thuật/đá tự nhiên, VRV/VRF, smart home.",
 cost=dict(structure="Suất vốn chung cư 2025 (Bộ XD): 9,2 triệu đ/m² sàn (≤5 tầng) đến 19,9 triệu đ/m² sàn (45–50 tầng, 5 hầm) — chưa VAT",fitout="ƯỚC TÍNH: 9–15 triệu đ/m² sàn cho hoàn thiện + thiết bị bàn giao",sources=[QD425]),
 implications="Chi phí thiết bị chiếm tỷ trọng lớn → đàm phán thỏa thuận khung theo nhãn (TBVS, bếp, phụ kiện) cho cả danh mục dự án; khóa giá USD/EUR sớm vì tỷ giá; kiểm soát lead time nhập khẩu 12–20 tuần; mặt dựng kính là gói rủi ro tiến độ."),
dict(id="cao-cap",name="Cao cấp",def_="Căn hộ khoảng 70–120 triệu đ/m² thông thủy.",
 hn=R(price="Giá sơ cấp bình quân ~107 triệu đ/m² (Savills); nội đô 102 triệu đ/m² (CBRE)",trend="↓ CBRE: toàn thị trường 86 triệu đ/m² (−9% q/q, −6% n/n) — lần giảm đầu tiên sau 2 năm; Savills: giảm nhẹ q/q, tăng n/n",supply="3.100 căn mở bán Q3 (−42% q/q, Savills); ~6.200 căn (−28% q/q, CBRE, gồm Văn Giang)",absorption="39% (Savills); giao dịch ~3.900 căn, −66% n/n (CBRE)",inventory="n/a",projects="The Senique (CapitaLand), Masteri Grand Coast (Masterise), các phân khu Ocean City",sources=[SAV_HN,CBRE_HN]),
 hcm=R(price="Sơ cấp bình quân ~75 triệu đ/m² (CBRE); DKRA ~68,5 triệu đ/m² (TP.HCM & vùng phụ cận)",trend="↓ −2,3% q/q, +1% n/n (CBRE); thứ cấp giảm >10% ở một số dự án",supply="3.267 căn mở bán (−53% n/n, CBRE); DKRA chào bán 13.215 căn (gồm hàng tồn)",absorption="45% (CBRE); DKRA tiêu thụ 3.471/13.215 căn ≈ 26%",inventory="DKRA: phần lớn nguồn cung chào bán là hàng tồn",projects="Celesta Gold (Keppel), Vlasta Premier (Văn Phú), Trellia Cove (Nam Long), Essensia Sky (Phú Long)",sources=[CBRE_HCM,DKRA,DKRA_PDF]),
 spec="TBVS Kohler/Grohe/TOTO, bếp Bosch, phụ kiện Hafele, khóa Hafele/Yale; điều hòa multi/cục bộ inverter; sàn gỗ công nghiệp hoặc gạch porcelain khổ lớn.",
 cost=dict(structure="Suất vốn chung cư 2025 (Bộ XD): 9,2–19,9 triệu đ/m² sàn theo số tầng/hầm — chưa VAT",fitout="ƯỚC TÍNH: 5–9 triệu đ/m² sàn hoàn thiện + thiết bị",sources=[QD425,PRIVE]),
 implications="Giá bán đang giảm ở HN → áp lực cắt chi phí; ưu tiên thay thế tương đương (VN/Trung Quốc OEM cho gạch, tủ bếp, cửa) ở hạng mục không thấy nhãn; giữ nhãn ở TBVS/bếp vì là điểm bán hàng."),
dict(id="trung-cap",name="Trung cấp",def_="Căn hộ khoảng 40–70 triệu đ/m², chủ yếu đại đô thị ven/ngoại thành.",
 hn=R(price="Từ ~55 triệu đ/m² (The CityOn, Ocean Park 3); thứ cấp toàn thị trường ~75 triệu đ/m² (Savills)",trend="→ CĐT dùng chính sách hỗ trợ lãi 36–60 tháng, chiết khấu thanh toán sớm ~13% thay vì giảm giá niêm yết",supply=">50% nguồn cung mới Q3 từ đại đô thị Văn Giang (Hưng Yên) — CBRE",absorption="Hạng B chiếm 73% giao dịch (Savills)",inventory="n/a",projects="The CityOn (MIK), Vinhomes Ocean Park 2/3 (Vinhomes)",sources=[CITYON,CBRE_HN,SAV_HN]),
 hcm=R(price="~45–70 triệu đ/m² (ước tính từ khoảng giá DKRA; bình quân DKRA 68,5 triệu đ/m²)",trend="↑ cầu nhà vừa túi tiền hút khách (Tuổi Trẻ, 15/10/2026)",supply="Akari City GĐ3 >1.200 sản phẩm (Nam Long), Izumi City",absorption="n/a",inventory="n/a",projects="Akari City, Mizuki Park (Nam Long), Vinhomes Grand Park (Vinhomes)",sources=[DKRA,S("Tuổi Trẻ – nhà vừa túi tiền hút khách","https://tuoitre.vn/bat-dong-san-tphcm-giang-co-ve-gia-nha-vua-tui-tien-hut-khach-100261015065846226.htm","2026-10-15")]),
 spec="TBVS nội địa/liên doanh (Inax, Viglacera, Caesar), bếp cơ bản, gạch ceramic/porcelain nội địa, điều hòa chờ (không lắp) hoặc cục bộ.",
 cost=dict(structure="Suất vốn chung cư 2025 (Bộ XD): 9,2–19,9 triệu đ/m² sàn — chưa VAT",fitout="ƯỚC TÍNH: 3–5 triệu đ/m² sàn",sources=[QD425]),
 implications="Cạnh tranh bằng giá → tối ưu kết cấu (thép, bê tông M350–M400), gom thầu khối lượng lớn với NCC nội địa; vật tư hoàn thiện ưu tiên VN (gạch đang dư cung, chạy ~50% công suất)."),
dict(id="noxh",name="Bình dân / NOXH",def_="Nhà ở xã hội, nhà ở cho thuê, nhà vừa túi tiền.",
 hn=R(price="Theo khung giá UBND tỉnh/thành phê duyệt cho từng dự án (không có giá thị trường chung)",trend="↑ chính sách thúc đẩy mạnh",supply="Cả nước 9T/2026: hoàn thành 170 dự án, 46.962 căn (38.183 căn bán/thuê mua, 8.314 căn cho thuê)",absorption="n/a",inventory="n/a",projects="Theo danh mục Bộ Xây dựng (hơn 910.000 căn đang triển khai cả nước)",sources=[NOXH,NOXH2]),
 hcm=R(price="Như cột Hà Nội — khung giá do địa phương phê duyệt",trend="↑",supply="Số liệu cả nước (xem cột HN)",absorption="n/a",inventory="n/a",projects="Theo danh mục Bộ Xây dựng",sources=[NOXH]),
 spec="Hoàn thiện cơ bản theo tiêu chuẩn tối thiểu; thiết bị nội địa giá thấp.",
 cost=dict(structure="Suất vốn chung cư 2025 (Bộ XD): 9,2–19,9 triệu đ/m² sàn — chưa VAT; lợi nhuận định mức NOXH bị khống chế",fitout="ƯỚC TÍNH: 1,5–3 triệu đ/m² sàn",sources=[QD425]),
 implications="Không phải phân khúc chính của Masterise, nhưng là nguồn cầu lớn cho thép, xi măng, gạch → ảnh hưởng giá vật liệu cơ bản 2027; theo dõi để chốt hợp đồng thép/xi măng sớm."),
dict(id="thap-tang",name="Biệt thự / liền kề / thấp tầng",def_="Biệt thự, liền kề, nhà phố, shophouse trong dự án.",
 hn=R(price="247 triệu đ/m² đất bình quân sơ cấp (chưa VAT, CBRE)",trend="↑ +18% q/q, +33% n/n",supply="1.517 căn mở bán Q3 (+37% q/q, +144% n/n)",absorption="~30% (hơn 500 căn); giao dịch chủ yếu từ dự án cũ",inventory="n/a",projects="Vinhomes Olympic Ngọc Hồi, Ocean City; khu Tây Hà Nội (Metro 5, Hòa Lạc)",sources=[VILLA,VILLA2]),
 hcm=R(price="214 triệu đ/m² đất (CBRE)",trend="↓ −0,6% q/q, −29% n/n",supply="30 căn mở bán mới Q3",absorption="n/a",inventory="n/a",projects="Rừng Phượng – Eco Retreat (Ecopark, Long An), các dự án vùng phụ cận",sources=[VILLA]),
 spec="Thường bàn giao thô/hoàn thiện mặt ngoài; khách tự hoàn thiện nội thất.",
 cost=dict(structure="ƯỚC TÍNH: phần thô + hoàn thiện ngoài 7–10 triệu đ/m² sàn (đối chiếu suất vốn nhà ở riêng lẻ QĐ 425)",fitout="Phần lớn do khách hàng tự làm",sources=[QD425]),
 implications="Nhu cầu lớn về cửa nhôm/kính, đá ốp mặt tiền, mái; thấp tầng HN đang nóng → giá nhân công & vật tư hoàn thiện ngoài vùng ven HN có thể tăng."),
dict(id="nghi-duong",name="Condotel / nghỉ dưỡng",def_="Condotel, biệt thự nghỉ dưỡng, khách sạn.",
 hn=R(price="n/a (thị trường chính ở miền Trung, Phú Quốc)",trend="↑ tiêu thụ cả nước Q3 tăng 5,4 lần q/q",supply="Cả nước ~6.300 căn chào bán, 79% là hàng tồn (DKRA)",absorption="932 căn tiêu thụ Q3; 75% đến từ một dự án mới",inventory="~79% nguồn cung là tồn kho",projects="Phú Quốc – APEC 2027 (Sun Group, nội thất Gold Mantis)",sources=[COND]),
 hcm=R(price="n/a",trend="Như cột trái (số liệu cả nước)",supply="Miền Trung chiếm >83% giao dịch",absorption="n/a",inventory="n/a",projects="Blanca City (Sun Group)",sources=[COND]),
 spec="Fit-out khách sạn theo brand standard của nhà vận hành (Marriott, IHG…).",
 cost=dict(structure="Theo suất vốn khách sạn QĐ 425",fitout="ƯỚC TÍNH: FF&E + fit-out 15–30 triệu đ/m² sàn tùy hạng sao",sources=[QD425]),
 implications="Nhà thầu fit-out Trung Quốc (Gold Mantis) vào VN → thêm lựa chọn và áp lực giá cho gói nội thất trọn gói."),
dict(id="van-phong",name="Văn phòng / bán lẻ",def_="Văn phòng hạng A/B, TTTM, mặt bằng bán lẻ.",
 hn=R(price="Văn phòng hạng A 29,8 USD/m²/tháng (+0,5% q/q); bán lẻ 44,8 USD/m²/tháng (chưa phí dịch vụ & VAT)",trend="→ tăng nhẹ",supply="n/a",absorption="Lấp đầy văn phòng hạng A 73,1% (giảm); bán lẻ 88,8%",inventory="Diện tích trống văn phòng hạng A ~27%",projects="Tổ hợp khách sạn–văn phòng Đông Anh (Newtecons)",sources=[NAI,NAI2]),
 hcm=R(price="Văn phòng hạng A 48,2 USD/m²/tháng (+0,7% q/q)",trend="↑ nhẹ",supply="n/a",absorption="Lấp đầy văn phòng hạng A 86,2%; bán lẻ ~93%",inventory="Diện tích trống hạng A ~14%",projects="Tháp đôi tứ giác Bến Thành (Newtecons)",sources=[NAI,NAI2]),
 spec="Bàn giao vỏ + core (shell & core), MEP trung tâm; fit-out do khách thuê.",
 cost=dict(structure="Theo suất vốn văn phòng QĐ 425",fitout="Fit-out khách thuê: không thuộc CĐT",sources=[QD425]),
 implications="HN dư diện tích trống → ít dự án văn phòng mới; nguồn lực MEP lớn (Hawee, REE, Sigma) chuyển sang trung tâm dữ liệu & sân bay → giá MEP có thể tăng nếu cầu data center giữ nhịp."),
]
for s in segs: s["def"]=s.pop("def_")
out=dict(period="Q3/2026",updated="2026-10-22",national=dict(text="VARS Q3/2026 (cả nước): 31.844 sản phẩm nhà ở mở bán mới, 12.520 giao dịch, hấp thụ 39,3% — thấp nhất 2 năm; căn hộ chiếm 67,27% nguồn cung.",sources=[VARS,KF]),
 note="Giá căn hộ là giá thông thủy, chưa VAT & phí bảo trì, trừ khi ghi khác. Dòng 'ƯỚC TÍNH' là ước tính nội bộ để định hướng, cần đối chiếu dự toán thực tế.",segments=segs)
json.dump(out,open("trends/data/segments.json","w"),ensure_ascii=False,indent=1);print(len(segs))
