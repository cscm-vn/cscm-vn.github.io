# Khởi tạo trends/data/brands.json (13/11/2026): danh bạ thương hiệu theo danh mục cấp 2 + phân khúc định vị tại VN.
# Phân khúc = định vị giá phổ biến trên thị trường VN (biên tập, tham khảo) – một hãng có nhiều dòng; xác nhận lại theo báo giá thực tế.
# kws: từ khoá KHÔNG DẤU, khớp nguyên từ trong tiêu đề tin (trends/brand_feed.py). Tên dễ trùng (Trần Phú, Tiền Phong, Bình Minh, TOA…) dùng cụm có ngữ cảnh.
# Giữ nguyên các trường biên tập (digest, cats[].digest) nếu brands.json đã có – script này chỉ (re)sinh danh bạ.
import json, os, unicodedata
N = lambda s: unicodedata.normalize("NFC", s)
p = "trends/data/brands.json"; old = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
TIERS = [
 dict(id="hang-sang", name="Hạng sang", use="Branded residence, penthouse, biệt thự hạng sang"),
 dict(id="cao-cap", name="Cao cấp", use="Căn hộ cao cấp, khu vực tiện ích chung, khách sạn 5 sao"),
 dict(id="trung-cap", name="Trung cấp", use="Căn hộ trung cấp, hạng mục kỹ thuật/khu vực phụ"),
 dict(id="pho-thong", name="Phổ thông", use="NOXH, khu kỹ thuật, hạng mục tạm/BOH"),
]
# (id, tên, xuất xứ thương hiệu, tập đoàn/ghi chú, kws, truy vấn Google News, {danh mục: phân khúc})
R = [
 # ---- Thiết bị vệ sinh
 ("duravit", "Duravit", "Đức", "", ["duravit"], '"Duravit"', {"ht.tbvs": "hang-sang"}),
 ("villeroy-boch", "Villeroy & Boch", "Đức", "", ["villeroy"], '"Villeroy"', {"ht.tbvs": "hang-sang"}),
 ("axor", "Axor", "Đức", "Dòng hạng sang của Hansgrohe", ["axor"], '"Axor" sen vòi', {"ht.tbvs": "hang-sang"}),
 ("gessi", "Gessi", "Ý", "", ["gessi"], '"Gessi"', {"ht.tbvs": "hang-sang"}),
 ("kohler", "Kohler", "Mỹ", "", ["kohler"], '"Kohler"', {"ht.tbvs": "cao-cap"}),
 ("grohe", "Grohe", "Đức", "Thuộc LIXIL", ["grohe"], '"Grohe"', {"ht.tbvs": "cao-cap"}),
 ("toto", "TOTO", "Nhật Bản", "", ["toto"], '"TOTO"', {"ht.tbvs": "cao-cap"}),
 ("hansgrohe", "Hansgrohe", "Đức", "", ["hansgrohe"], '"Hansgrohe"', {"ht.tbvs": "cao-cap"}),
 ("american-standard", "American Standard", "Mỹ", "Thuộc LIXIL", ["american standard"], '"American Standard"', {"ht.tbvs": "trung-cap"}),
 ("inax", "INAX", "Nhật Bản", "Thuộc LIXIL", ["inax", "lixil"], '"INAX" OR "LIXIL"', {"ht.tbvs": "trung-cap"}),
 ("caesar", "Caesar", "Đài Loan", "", ["thiet bi ve sinh caesar", "caesar"], '"Caesar" thiết bị vệ sinh', {"ht.tbvs": "trung-cap"}),
 ("viglacera", "Viglacera", "Việt Nam", "", ["viglacera", "vgc"], '"Viglacera"', {"ht.tbvs": "pho-thong", "ht.gach-da": "pho-thong", "md.kinh": "trung-cap"}),
 # ---- Thiết bị bếp
 ("gaggenau", "Gaggenau", "Đức", "Thuộc BSH", ["gaggenau"], '"Gaggenau"', {"ht.thiet-bi-bep": "hang-sang"}),
 ("miele", "Miele", "Đức", "", ["miele"], '"Miele"', {"ht.thiet-bi-bep": "hang-sang"}),
 ("sub-zero-wolf", "Sub-Zero & Wolf", "Mỹ", "", ["sub-zero", "sub zero"], '"Sub-Zero"', {"ht.thiet-bi-bep": "hang-sang"}),
 ("v-zug", "V-ZUG", "Thụy Sĩ", "", ["v-zug", "vzug"], '"V-ZUG"', {"ht.thiet-bi-bep": "hang-sang"}),
 ("bosch", "Bosch", "Đức", "Gia dụng thuộc BSH; mảng an ninh Bosch", ["bosch"], '"Bosch"', {"ht.thiet-bi-bep": "cao-cap", "elv.an-ninh": "cao-cap"}),
 ("siemens", "Siemens", "Đức", "Gia dụng thuộc BSH; thiết bị điện Siemens", ["siemens"], '"Siemens"', {"ht.thiet-bi-bep": "cao-cap", "mep.tu-dien": "cao-cap"}),
 ("smeg", "Smeg", "Ý", "", ["smeg"], '"Smeg"', {"ht.thiet-bi-bep": "cao-cap"}),
 ("hafele", "Häfele", "Đức", "Phân phối thiết bị bếp, phụ kiện nội thất, khóa", ["hafele"], '"Hafele" OR "Häfele"', {"ht.thiet-bi-bep": "trung-cap", "ht.tu-bep": "cao-cap", "ht.cua": "cao-cap"}),
 ("teka", "Teka", "Tây Ban Nha", "", ["teka"], '"Teka"', {"ht.thiet-bi-bep": "trung-cap"}),
 ("electrolux", "Electrolux", "Thụy Điển", "", ["electrolux"], '"Electrolux"', {"ht.thiet-bi-bep": "trung-cap"}),
 ("malloca", "Malloca", "Việt Nam / châu Á", "", ["malloca"], '"Malloca"', {"ht.thiet-bi-bep": "trung-cap"}),
 ("sunhouse", "Sunhouse", "Việt Nam", "", ["sunhouse"], '"Sunhouse"', {"ht.thiet-bi-bep": "pho-thong"}),
 ("canzy", "Canzy", "Việt Nam", "", ["canzy"], '"Canzy"', {"ht.thiet-bi-bep": "pho-thong"}),
 # ---- Tủ bếp & nội thất liền tường, phụ kiện
 ("poggenpohl", "Poggenpohl", "Đức", "", ["poggenpohl"], '"Poggenpohl"', {"ht.tu-bep": "hang-sang"}),
 ("bulthaup", "Bulthaup", "Đức", "", ["bulthaup"], '"Bulthaup"', {"ht.tu-bep": "hang-sang"}),
 ("siematic", "SieMatic", "Đức", "", ["siematic"], '"SieMatic"', {"ht.tu-bep": "hang-sang"}),
 ("blum", "Blum", "Áo", "Phụ kiện bản lề, ray, tay nâng", ["blum"], '"Blum" phụ kiện', {"ht.tu-bep": "cao-cap"}),
 ("hettich", "Hettich", "Đức", "Phụ kiện nội thất", ["hettich"], '"Hettich"', {"ht.tu-bep": "cao-cap"}),
 ("an-cuong", "An Cường", "Việt Nam", "Ván MFC/MDF, tủ bếp, nội thất dự án (HOSE: ACG)", ["go an cuong", "an cuong", "acg"], '"Gỗ An Cường" OR "An Cường" nội thất', {"ht.tu-bep": "trung-cap"}),
 ("oppein", "OPPEIN", "Trung Quốc", "Tủ bếp, tủ áo theo dự án", ["oppein"], '"OPPEIN"', {"ht.tu-bep": "trung-cap"}),
 # ---- Gạch ốp lát, đá, đá nung kết
 ("porcelanosa", "Porcelanosa", "Tây Ban Nha", "", ["porcelanosa"], '"Porcelanosa"', {"ht.gach-da": "hang-sang"}),
 ("florim", "Florim", "Ý", "", ["florim"], '"Florim"', {"ht.gach-da": "hang-sang"}),
 ("laminam", "Laminam", "Ý", "Tấm gốm mỏng khổ lớn", ["laminam"], '"Laminam"', {"ht.gach-da": "hang-sang"}),
 ("antolini", "Antolini", "Ý", "Đá tự nhiên", ["antolini"], '"Antolini"', {"ht.gach-da": "hang-sang"}),
 ("marazzi", "Marazzi", "Ý", "", ["marazzi"], '"Marazzi"', {"ht.gach-da": "cao-cap"}),
 ("atlas-concorde", "Atlas Concorde", "Ý", "", ["atlas concorde"], '"Atlas Concorde"', {"ht.gach-da": "cao-cap"}),
 ("neolith", "Neolith", "Tây Ban Nha", "Đá nung kết", ["neolith"], '"Neolith"', {"ht.gach-da": "cao-cap"}),
 ("prime", "Prime", "Việt Nam", "Thuộc SCG", ["gach prime", "prime group"], '"Prime Group" OR "gạch Prime"', {"ht.gach-da": "trung-cap"}),
 ("dong-tam", "Đồng Tâm", "Việt Nam", "", ["gach dong tam", "dong tam group", "dtl"], '"Đồng Tâm" gạch', {"ht.gach-da": "trung-cap"}),
 ("taicera", "Taicera", "Đài Loan", "", ["taicera"], '"Taicera"', {"ht.gach-da": "trung-cap"}),
 ("catalan", "Catalan", "Việt Nam", "", ["gach catalan"], '"gạch Catalan"', {"ht.gach-da": "pho-thong"}),
 # ---- Sàn gỗ / SPC / vinyl
 ("listone-giordano", "Listone Giordano", "Ý", "", ["listone giordano"], '"Listone Giordano"', {"ht.san": "hang-sang"}),
 ("kahrs", "Kährs", "Thụy Điển", "", ["kahrs"], '"Kahrs" OR "Kährs"', {"ht.san": "cao-cap"}),
 ("quick-step", "Quick-Step", "Bỉ", "Thuộc Unilin", ["quick-step", "quickstep"], '"Quick-Step" sàn', {"ht.san": "cao-cap"}),
 ("pergo", "Pergo", "Bỉ", "Thuộc Unilin", ["pergo"], '"Pergo"', {"ht.san": "cao-cap"}),
 ("egger", "Egger", "Áo", "", ["egger"], '"Egger"', {"ht.san": "trung-cap"}),
 ("inovar", "Inovar", "Malaysia", "", ["inovar"], '"Inovar"', {"ht.san": "trung-cap"}),
 ("robina", "Robina", "Malaysia", "", ["robina"], '"Robina" sàn gỗ', {"ht.san": "trung-cap"}),
 # ---- Sơn
 ("jotun", "Jotun", "Na Uy", "", ["jotun"], '"Jotun"', {"ht.son": "cao-cap"}),
 ("dulux", "Dulux", "Hà Lan/Anh", "Thuộc AkzoNobel", ["dulux", "akzonobel"], '"Dulux" OR "AkzoNobel"', {"ht.son": "cao-cap"}),
 ("nippon-paint", "Nippon Paint", "Nhật Bản", "", ["nippon paint", "son nippon"], '"Nippon Paint"', {"ht.son": "cao-cap"}),
 ("toa", "TOA", "Thái Lan", "", ["son toa", "toa paint"], '"sơn TOA" OR "TOA Paint"', {"ht.son": "trung-cap"}),
 ("kova", "Kova", "Việt Nam", "", ["son kova", "kova"], '"sơn Kova"', {"ht.son": "trung-cap"}),
 ("maxilite", "Maxilite", "Hà Lan/Anh", "Dòng kinh tế của AkzoNobel", ["maxilite"], '"Maxilite"', {"ht.son": "pho-thong"}),
 # ---- Cửa, khóa & phụ kiện
 ("dormakaba", "dormakaba", "Thụy Sĩ", "Khóa, phụ kiện cửa, cửa tự động", ["dormakaba"], '"dormakaba"', {"ht.cua": "cao-cap"}),
 ("assa-abloy", "ASSA ABLOY", "Thụy Điển", "", ["assa abloy"], '"Assa Abloy"', {"ht.cua": "cao-cap"}),
 ("yale", "Yale", "Thụy Điển", "Thuộc ASSA ABLOY", ["khoa yale", "yale lock"], '"khóa Yale"', {"ht.cua": "trung-cap"}),
 ("austdoor", "Austdoor", "Việt Nam", "Cửa cuốn, cửa chống cháy, nhôm Topal", ["austdoor", "topal"], '"Austdoor"', {"ht.cua": "trung-cap", "md.nhom": "trung-cap"}),
 ("viet-tiep", "Việt Tiệp", "Việt Nam", "", ["khoa viet tiep"], '"khóa Việt Tiệp"', {"ht.cua": "pho-thong"}),
 # ---- Kính
 ("saint-gobain", "Saint-Gobain", "Pháp", "", ["saint-gobain", "saint gobain"], '"Saint-Gobain"', {"md.kinh": "cao-cap"}),
 ("agc", "AGC", "Nhật Bản", "", ["agc glass", "kinh agc", "agc"], '"AGC" kính', {"md.kinh": "cao-cap"}),
 ("guardian", "Guardian Glass", "Mỹ", "", ["guardian glass"], '"Guardian Glass"', {"md.kinh": "cao-cap"}),
 ("xinyi", "Xinyi Glass", "Trung Quốc", "", ["xinyi"], '"Xinyi"', {"md.kinh": "trung-cap"}),
 ("taiwan-glass", "Taiwan Glass", "Đài Loan", "", ["taiwan glass"], '"Taiwan Glass"', {"md.kinh": "trung-cap"}),
 # ---- Hệ nhôm
 ("schuco", "Schüco", "Đức", "", ["schuco", "schueco"], '"Schüco" OR "Schuco"', {"md.nhom": "hang-sang"}),
 ("reynaers", "Reynaers", "Bỉ", "", ["reynaers"], '"Reynaers"', {"md.nhom": "hang-sang"}),
 ("technal", "Technal", "Pháp", "Thuộc Hydro", ["technal"], '"Technal"', {"md.nhom": "cao-cap"}),
 ("ykk-ap", "YKK AP", "Nhật Bản", "", ["ykk ap", "ykk"], '"YKK AP"', {"md.nhom": "cao-cap"}),
 ("eurowindow", "Eurowindow", "Việt Nam", "Cửa uPVC/nhôm", ["eurowindow"], '"Eurowindow"', {"md.nhom": "trung-cap"}),
 ("xingfa", "Xingfa", "Trung Quốc", "Hệ nhôm phổ biến tại VN (nhiều hàng nhái tên)", ["xingfa"], '"Xingfa"', {"md.nhom": "trung-cap"}),
 ("viet-phap", "Nhôm Việt Pháp", "Việt Nam", "", ["nhom viet phap"], '"nhôm Việt Pháp"', {"md.nhom": "pho-thong"}),
 # ---- Mặt dựng
 ("alucobond", "Alucobond", "Đức", "Tấm ACP (3A Composites)", ["alucobond"], '"Alucobond"', {"md.mat-dung": "cao-cap"}),
 ("alpolic", "Alpolic", "Nhật Bản", "Tấm ACP (Mitsubishi Chemical)", ["alpolic"], '"Alpolic"', {"md.mat-dung": "cao-cap"}),
 ("hunter-douglas", "Hunter Douglas", "Hà Lan", "Lam, trần, rèm", ["hunter douglas"], '"Hunter Douglas"', {"md.mat-dung": "cao-cap"}),
 # ---- HVAC
 ("daikin", "Daikin", "Nhật Bản", "", ["daikin"], '"Daikin"', {"mep.hvac": "cao-cap"}),
 ("mitsubishi-electric", "Mitsubishi Electric", "Nhật Bản", "Điều hòa, thang máy, thiết bị điện", ["mitsubishi electric"], '"Mitsubishi Electric"', {"mep.hvac": "cao-cap", "mep.thang-may": "cao-cap"}),
 ("trane", "Trane", "Mỹ", "Chiller", ["trane"], '"Trane"', {"mep.hvac": "cao-cap"}),
 ("carrier", "Carrier", "Mỹ", "", ["dieu hoa carrier", "carrier vietnam", "carrier viet nam"], '"Carrier" điều hòa', {"mep.hvac": "cao-cap"}),
 ("lg", "LG", "Hàn Quốc", "", ["lg electronics", "lg"], '"LG" điều hòa', {"mep.hvac": "trung-cap"}),
 ("samsung", "Samsung", "Hàn Quốc", "", ["samsung"], '"Samsung" điều hòa', {"mep.hvac": "trung-cap"}),
 ("panasonic", "Panasonic", "Nhật Bản", "", ["panasonic"], '"Panasonic"', {"mep.hvac": "trung-cap"}),
 ("gree", "Gree", "Trung Quốc", "", ["gree"], '"Gree" điều hòa', {"mep.hvac": "pho-thong"}),
 ("midea", "Midea", "Trung Quốc", "", ["midea"], '"Midea"', {"mep.hvac": "pho-thong"}),
 ("reetech", "Reetech", "Việt Nam", "Thuộc REE", ["reetech"], '"Reetech"', {"mep.hvac": "pho-thong"}),
 # ---- Thang máy
 ("kone", "KONE", "Phần Lan", "", ["kone"], '"KONE" thang máy', {"mep.thang-may": "cao-cap"}),
 ("schindler", "Schindler", "Thụy Sĩ", "", ["schindler"], '"Schindler"', {"mep.thang-may": "cao-cap"}),
 ("otis", "Otis", "Mỹ", "", ["otis"], '"Otis" thang máy', {"mep.thang-may": "cao-cap"}),
 ("tk-elevator", "TK Elevator", "Đức", "", ["tk elevator", "thyssenkrupp"], '"TK Elevator" OR "thyssenkrupp" thang máy', {"mep.thang-may": "cao-cap"}),
 ("hitachi-elevator", "Hitachi (thang máy)", "Nhật Bản", "", ["thang may hitachi", "hitachi elevator"], '"thang máy Hitachi"', {"mep.thang-may": "cao-cap"}),
 ("fujitec", "Fujitec", "Nhật Bản", "", ["fujitec"], '"Fujitec"', {"mep.thang-may": "trung-cap"}),
 ("hyundai-elevator", "Hyundai Elevator", "Hàn Quốc", "", ["hyundai elevator", "thang may hyundai"], '"thang máy Hyundai"', {"mep.thang-may": "trung-cap"}),
 ("thien-nam", "Thiên Nam", "Việt Nam", "", ["thang may thien nam"], '"thang máy Thiên Nam"', {"mep.thang-may": "pho-thong"}),
 # ---- Dây & cáp điện
 ("ls-vina", "LS Cable / LS-VINA", "Hàn Quốc", "", ["ls-vina", "ls vina", "ls cable"], '"LS-VINA" OR "LS Cable"', {"mep.cap-dien": "cao-cap"}),
 ("cadivi", "Cadivi", "Việt Nam", "Thuộc GELEX", ["cadivi"], '"Cadivi"', {"mep.cap-dien": "cao-cap"}),
 ("taya", "Taya", "Đài Loan", "", ["taya"], '"Taya" cáp điện', {"mep.cap-dien": "trung-cap"}),
 ("tran-phu", "Cáp điện Trần Phú", "Việt Nam", "", ["cap dien tran phu", "day cap tran phu", "tran phu cable"], '"cáp điện Trần Phú" OR "dây cáp Trần Phú"', {"mep.cap-dien": "trung-cap"}),
 ("daphaco", "Daphaco", "Việt Nam", "", ["daphaco"], '"Daphaco"', {"mep.cap-dien": "pho-thong"}),
 ("cadisun", "Cadisun", "Việt Nam", "", ["cadisun"], '"Cadisun"', {"mep.cap-dien": "pho-thong"}),
 # ---- Ống nước
 ("aquatherm", "Aquatherm", "Đức", "Ống PPR", ["aquatherm"], '"Aquatherm"', {"mep.ong-nuoc": "cao-cap"}),
 ("rehau", "Rehau", "Đức", "", ["rehau"], '"Rehau"', {"mep.ong-nuoc": "cao-cap"}),
 ("wavin", "Wavin", "Hà Lan", "", ["wavin"], '"Wavin"', {"mep.ong-nuoc": "cao-cap"}),
 ("tien-phong", "Nhựa Tiền Phong", "Việt Nam", "HNX: NTP", ["nhua tien phong", "ntp"], '"Nhựa Tiền Phong"', {"mep.ong-nuoc": "trung-cap"}),
 ("binh-minh", "Nhựa Bình Minh", "Việt Nam", "HOSE: BMP", ["nhua binh minh", "bmp"], '"Nhựa Bình Minh"', {"mep.ong-nuoc": "trung-cap"}),
 ("hoa-sen", "Nhựa Hoa Sen", "Việt Nam", "Thuộc Tập đoàn Hoa Sen", ["nhua hoa sen", "tap doan hoa sen", "hsg"], '"Hoa Sen" ống nhựa', {"mep.ong-nuoc": "pho-thong"}),
 ("de-nhat", "Nhựa Đệ Nhất", "Việt Nam", "", ["nhua de nhat"], '"nhựa Đệ Nhất"', {"mep.ong-nuoc": "pho-thong"}),
 # ---- Tủ điện, thiết bị đóng cắt
 ("schneider", "Schneider Electric", "Pháp", "Thiết bị đóng cắt, nhà thông minh Wiser", ["schneider"], '"Schneider Electric"', {"mep.tu-dien": "cao-cap", "elv.smart-home": "cao-cap"}),
 ("abb", "ABB", "Thụy Sĩ", "", ["abb"], '"ABB"', {"mep.tu-dien": "cao-cap"}),
 ("ls-electric", "LS Electric", "Hàn Quốc", "", ["ls electric"], '"LS Electric"', {"mep.tu-dien": "trung-cap"}),
 ("chint", "Chint", "Trung Quốc", "", ["chint"], '"Chint"', {"mep.tu-dien": "trung-cap"}),
 ("sino", "Sino (Vanlock)", "Việt Nam", "", ["sino vanlock", "vanlock"], '"Vanlock" OR "Sino Vanlock"', {"mep.tu-dien": "pho-thong"}),
 # ---- Máy phát, máy biến áp
 ("cummins", "Cummins", "Mỹ", "", ["cummins"], '"Cummins"', {"mep.may-phat": "cao-cap"}),
 ("caterpillar", "Caterpillar", "Mỹ", "", ["caterpillar"], '"Caterpillar" máy phát', {"mep.may-phat": "cao-cap"}),
 ("mtu", "MTU (Rolls-Royce)", "Đức", "", ["mtu"], '"MTU" máy phát', {"mep.may-phat": "cao-cap"}),
 ("hitachi-energy", "Hitachi Energy", "Thụy Sĩ / Nhật Bản", "Máy biến áp", ["hitachi energy"], '"Hitachi Energy"', {"mep.may-phat": "cao-cap"}),
 ("thibidi", "THIBIDI", "Việt Nam", "Máy biến áp, thuộc GELEX", ["thibidi"], '"THIBIDI"', {"mep.may-phat": "trung-cap"}),
 ("eemc", "EEMC (Thiết bị điện Đông Anh)", "Việt Nam", "Máy biến áp, thuộc GELEX", ["eemc", "thiet bi dien dong anh"], '"EEMC" OR "Thiết bị điện Đông Anh"', {"mep.may-phat": "trung-cap"}),
 ("huu-toan", "Hữu Toàn", "Việt Nam", "Máy phát lắp ráp", ["may phat huu toan"], '"máy phát Hữu Toàn"', {"mep.may-phat": "pho-thong"}),
 # ---- PCCC
 ("tyco", "Tyco", "Mỹ", "Thuộc Johnson Controls", ["tyco", "johnson controls"], '"Tyco" OR "Johnson Controls"', {"mep.pccc": "cao-cap"}),
 ("honeywell", "Honeywell", "Mỹ", "Báo cháy (Notifier), an ninh", ["honeywell", "notifier"], '"Honeywell"', {"mep.pccc": "cao-cap", "elv.an-ninh": "cao-cap"}),
 ("hochiki", "Hochiki", "Nhật Bản", "Báo cháy", ["hochiki"], '"Hochiki"', {"mep.pccc": "cao-cap"}),
 ("horing", "Horing Lih", "Đài Loan", "Báo cháy", ["horing"], '"Horing"', {"mep.pccc": "trung-cap"}),
 # ---- Nhà thông minh
 ("crestron", "Crestron", "Mỹ", "", ["crestron"], '"Crestron"', {"elv.smart-home": "hang-sang"}),
 ("control4", "Control4", "Mỹ", "Thuộc Snap One", ["control4"], '"Control4"', {"elv.smart-home": "hang-sang"}),
 ("lumi", "Lumi", "Việt Nam", "", ["lumi smart", "lumi viet nam", "lumi smarthome"], '"Lumi" nhà thông minh', {"elv.smart-home": "trung-cap"}),
 ("bkav-smarthome", "BKAV SmartHome", "Việt Nam", "", ["bkav smarthome", "bkav smart home"], '"Bkav SmartHome"', {"elv.smart-home": "trung-cap"}),
 ("aqara", "Aqara", "Trung Quốc", "", ["aqara"], '"Aqara"', {"elv.smart-home": "pho-thong"}),
 # ---- An ninh, camera
 ("axis", "Axis Communications", "Thụy Điển", "", ["axis communications"], '"Axis Communications"', {"elv.an-ninh": "cao-cap"}),
 ("hanwha-vision", "Hanwha Vision", "Hàn Quốc", "", ["hanwha vision"], '"Hanwha Vision"', {"elv.an-ninh": "trung-cap"}),
 ("hikvision", "Hikvision", "Trung Quốc", "", ["hikvision"], '"Hikvision"', {"elv.an-ninh": "pho-thong"}),
 ("dahua", "Dahua", "Trung Quốc", "", ["dahua"], '"Dahua"', {"elv.an-ninh": "pho-thong"}),
]
# Ngữ cảnh truy vấn Google News theo danh mục (giảm nhiễu: Samsung điện thoại, Bosch ô tô…)
CTX = {
 "ht.tbvs": "(vệ sinh OR bồn OR sen OR vòi OR nhà tắm OR showroom)", "ht.thiet-bi-bep": "(bếp OR gia dụng OR máy rửa bát OR tủ lạnh OR lò)",
 "ht.tu-bep": "(tủ bếp OR nội thất OR phụ kiện OR gỗ)", "ht.gach-da": "(gạch OR đá OR gốm OR ốp lát)", "ht.san": "(sàn OR gỗ OR vinyl)",
 "ht.son": "(sơn OR phủ)", "ht.cua": "(khóa OR cửa OR phụ kiện)", "md.kinh": "(kính OR glass)", "md.nhom": "(nhôm OR cửa OR mặt dựng)",
 "md.mat-dung": "(mặt dựng OR ốp OR lam OR tấm)", "mep.hvac": "(điều hòa OR HVAC OR chiller OR làm lạnh)", "mep.thang-may": "(thang máy OR thang cuốn)",
 "mep.cap-dien": "(cáp OR dây điện OR đồng)", "mep.ong-nuoc": "(ống OR nhựa)", "mep.tu-dien": "(điện OR tủ điện OR thiết bị)",
 "mep.may-phat": "(máy phát OR máy biến áp OR điện)", "mep.pccc": "(PCCC OR báo cháy OR chữa cháy OR an ninh)",
 "elv.smart-home": "(nhà thông minh OR smart home OR căn hộ)", "elv.an-ninh": "(camera OR an ninh OR kiểm soát ra vào)",
}
ob = {b["id"]: b for b in old.get("brands", [])}
brands = []
for bid, name, origin, note, kws, q, tax in R:
    b = dict(id=bid, name=N(name), origin=N(origin), note=N(note), kws=kws, query=N(q), tax=tax)
    for k in ("digest", "web"):  # trường biên tập do lịch tuần cập nhật
        if k in ob.get(bid, {}): b[k] = ob[bid][k]
    brands.append(b)
cats = {c: dict(ctx=N(CTX[c]), **{k: v for k, v in old.get("cats", {}).get(c, {}).items() if k != "ctx"}) for c in CTX}
assert len({b["id"] for b in brands}) == len(brands) and all(t in CTX for b in brands for t in b["tax"])
assert all(v in {t["id"] for t in TIERS} for b in brands for v in b["tax"].values())
d = dict(schema_version=1, updated=old.get("updated", "2026-11-13"), registry_updated="2026-11-13",
         note=N("Phân khúc = định vị giá phổ biến tại VN (biên tập, tham khảo); một hãng có nhiều dòng sản phẩm – xác nhận theo báo giá/hồ sơ dự án."),
         tiers=[{k: N(v) for k, v in t.items()} for t in TIERS], cats=cats, brands=brands)
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("brands:", len(brands), "cats:", len(cats))
