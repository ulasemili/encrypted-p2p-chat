# Şifreli P2P Haberleşme Uygulaması

Bu proje, aynı ağdaki iki bilgisayarın merkezi sunucu kullanmadan doğrudan TCP/IP üzerinden haberleşmesini sağlar. Mesaj içerikleri ağda açık metin olarak gitmez. Mesajlar 6x6 Türkçe Playfair algoritmasıyla şifrelenir.

Bu sürümde bağlantıyı kuran kişi, o mesajlaşmada kullanılacak Playfair anahtarını kendisi belirler. Bu anahtar karşı tarafa açık şekilde gönderilmez. Önce Diffie-Hellman tabanlı güvenli anahtar değişimi yapılır, sonra Playfair anahtarı bu güvenli kanal üzerinden şifrelenerek karşı tarafa iletilir.

## Temel özellikler

- Python 3 ile Windows, macOS ve Linux desteği
- CustomTkinter ile masaüstü arayüz
- TCP/IP socket ile P2P bağlantı
- Threading ile arayüz donmadan mesaj alma
- SQLite ile yerel kullanıcı ve mesaj geçmişi kaydı
- SHA-256 ile parola hashleme
- 29 Türkçe harf + 7 karakter içeren 6x6 Playfair şifreleme
- RSA kullanmadan Diffie-Hellman tabanlı güvenli anahtar paylaşımı
- Mesajların ekranda önce şifreli görünmesi
- Mesaja tıklayınca açık metnin gösterilmesi
- Oturum anahtarının ekranda doğrudan görünmemesi, sadece butona basınca gösterilmesi

## Klasör yapısı

```text
encrypted_p2p_chat/
│
├── run.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── app/
    ├── config.py
    ├── crypto/
    │   ├── playfair.py
    │   └── key_exchange.py
    ├── db/
    │   └── database.py
    ├── network/
    │   └── peer.py
    ├── ui/
    │   ├── login_window.py
    │   └── chat_window.py
    └── utils/
        └── helpers.py
```

## Şifreleme sistemi nasıl çalışır?

Sistem iki aşamalı çalışır.

### 1. Playfair anahtarını güvenli paylaşma

Bağlantıyı başlatan kişi, arayüzdeki `Bu mesajlaşmanın Playfair anahtarı` alanına bir anahtar yazar. Varsayılan değer `türkiyem!` olarak gelir ama istenirse değiştirilebilir.

Bu anahtar karşı tarafa düz metin olarak gönderilmez. Bağlantı kurulunca iki taraf geçici anahtarlar üretir ve Diffie-Hellman mantığıyla ortak bir gizli değer oluşturur. Bu gizli değerden geçici bir şifreleme anahtarı türetilir. Bağlantıyı başlatan kişinin yazdığı Playfair anahtarı bu geçici anahtarla şifrelenerek karşı tarafa gönderilir.

Bu aşamada amaç yalnızca Playfair oturum anahtarını güvenli paylaşmaktır. Mesajların kendisi Diffie-Hellman ile şifrelenmez.

Ağda açık giden bilgiler:

```text
public key değerleri
kullanıcı adı
paket tipi
zaman bilgisi
```

Ağda açık gitmeyen bilgiler:

```text
Playfair oturum anahtarı
mesajların açık hali
```

### 2. Mesajları Playfair ile şifreleme

İki tarafta da aynı Playfair oturum anahtarı hazır olunca mesajlar 6x6 Türkçe Playfair algoritmasıyla şifrelenir.

Matris karakterleri:

```text
29 Türkçe harf:
a b c ç d e f g ğ h ı i j k l m n o ö p r s ş t u ü v y z

7 ek karakter:
boşluk . , ? ! : ^
```

`^` karakteri teknik dolgu karakteridir. Aynı iki karakter yan yana geldiğinde veya mesaj tek karakterle bittiğinde Playfair algoritmasının ikili gruplama mantığı için kullanılır.

## Arayüzde mesajlar neden şifreli görünüyor?

Mesaj balonları ilk geldiğinde veya gönderildiğinde yalnızca şifreli metni gösterir. Balonun içinde gönderen adı veya açıklama yazısı bulunmaz. Açık metni görmek için mesaj balonuna tıklaman gerekir. Tıkladıktan sonra o mesaj açık hale geçer.

Bu davranış, sunumda şunu göstermek için özellikle eklenmiştir:

```text
Ağda ve uygulamanın ilk görüntüsünde mesaj ciphertext olarak durur.
Kullanıcı isteyince, doğru oturum anahtarıyla plaintext elde edilir.
```

## İlk kurulum - Mac

### 1. Homebrew yoksa kur

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 2. Python ve Tkinter kur

```bash
brew install python@3.12
brew install python-tk@3.12
```

### 3. Proje klasörüne gir

ZIP dosyasını Downloads içine çıkardıysan:

```bash
cd ~/Downloads/encrypted_p2p_chat
```

### 4. Sanal ortam oluştur

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 5. Gerekli paketleri kur

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Uygulamayı çalıştır

```bash
export TK_SILENCE_DEPRECATION=1
python run.py
```

## İlk kurulum - Windows

### 1. Python kur

Önerilen yöntem: `python.org` üzerinden Python 3.12 kurmak.

Kurulum ekranında şu seçenek işaretli olmalı:

```text
Add python.exe to PATH
```

Microsoft Store Python kullanıyorsan da çalışabilir. Kontrol için PowerShell'de şunu deneyebilirsin:

```powershell
python --version
python -m tkinter
```

`python -m tkinter` küçük bir pencere açıyorsa Tkinter vardır.

### 2. Proje klasörüne gir

ZIP dosyasını Downloads içine çıkardıysan:

```powershell
cd Downloads\encrypted_p2p_chat
```

### 3. Sanal ortam oluştur

```powershell
python -m venv .venv
```

veya:

```powershell
py -3.12 -m venv .venv
```

### 4. Sanal ortamı aktif et

```powershell
.\.venv\Scripts\Activate.ps1
```

İzin hatası alırsan bir kez şunu çalıştır:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Sonra tekrar aktif et:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 5. Gerekli paketleri kur

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Uygulamayı çalıştır

```powershell
python run.py
```

Windows Güvenlik Duvarı uyarı verirse Python için özel ağ erişimine izin ver.

## İkinci ve sonraki çalıştırmalar

Kurulum bir kez yapıldıktan sonra her seferinde `pip install` yapmana gerek yoktur.

Mac:

```bash
cd ~/Downloads/encrypted_p2p_chat
source .venv/bin/activate
export TK_SILENCE_DEPRECATION=1
python run.py
```

Windows:

```powershell
cd Downloads\encrypted_p2p_chat
.\.venv\Scripts\Activate.ps1
python run.py
```

## İki bilgisayarda test etme

1. İki bilgisayar aynı Wi-Fi veya LAN ağına bağlı olsun.
2. İki bilgisayarda da uygulamayı aç.
3. İki bilgisayarda da kullanıcı oluşturup giriş yap.
4. İki bilgisayarda da `Dinlemeyi Başlat` butonuna bas.
5. Bağlantıyı başlatacak bilgisayarda karşı tarafın IP adresini ve portunu yaz.
6. Aynı bilgisayarda `Bu mesajlaşmanın Playfair anahtarı` alanına kullanılacak anahtarı yaz.
7. `Bağlan` butonuna bas.
8. Diffie-Hellman tabanlı değişim tamamlanınca iki tarafta da `Anahtar: güvenli oturum hazır` yazar.
9. Anahtarı görmek istersen `Oturum Anahtarını Göster` butonuna basabilirsin.
10. Mesaj gönder. Mesaj balonu önce şifreli görünür.
11. Mesajın açık halini görmek için mesaj balonuna tıkla.

## Sunumda kısa anlatım

Projede merkezi sunucu yoktur. Her uygulama aynı anda hem dinleyici hem gönderici gibi çalışır. Bağlantıyı kuran taraf, o oturumda kullanılacak Playfair anahtarını belirler. Bu anahtar ağda açık gönderilmez; önce Diffie-Hellman tabanlı geçici bir güvenli kanal oluşturulur, sonra Playfair anahtarı bu kanalda şifreli gönderilir. Bundan sonraki mesajların tamamı projeye özel 6x6 Türkçe Playfair algoritması ile şifrelenir. Mesajlar arayüzde de önce şifreli görünür; kullanıcı mesaj balonuna tıkladığında doğru oturum anahtarıyla çözülüp açık hale getirilir. Kullanıcı parolaları SQLite veritabanında açık değil SHA-256 hash olarak tutulur.

## Sorun giderme

### Uygulama açılmıyor

Mac'te Tkinter eksik olabilir:

```bash
brew install python-tk@3.12
```

Windows'ta Tkinter kontrolü:

```powershell
python -m tkinter
```

### Bağlantı kurulamıyor

Kontrol et:

```text
1. İki bilgisayar aynı ağda mı?
2. İki tarafta da Dinlemeyi Başlat butonuna basıldı mı?
3. IP adresi doğru mu?
4. Port iki tarafta da aynı mı? Varsayılan: 5050
5. Windows Güvenlik Duvarı Python'a özel ağ izni verdi mi?
6. Okul/modem ağı cihazların birbirini görmesini engelliyor olabilir mi?
```

### Mesaj çözülemiyor veya anlamsız çıkıyor

Bu sürümde anahtarı bağlantıyı başlatan kişi belirler ve karşı tarafa güvenli şekilde gönderilir. Yine de iki bilgisayarda farklı proje sürümleri çalışıyorsa sorun yaşanabilir. İki tarafta da aynı ZIP sürümünü kullan.
