# Ağ Ortamında Şifreli Haberleşme Yapan Bilgisayar Yazılımı

Bu proje, iki bilgisayarın aynı ağ içinde doğrudan birbirine bağlanarak şifreli mesajlaşmasını sağlayan masaüstü bir Python uygulamasıdır.

Projede merkezi bir sunucu yoktur. Her bilgisayar aynı anda hem dinleyici hem de gönderici olarak çalışır. Mesajlar TCP/IP socket ile gönderilir, arayüzün donmaması için ağ işlemleri ayrı thread üzerinde yürütülür, kullanıcı bilgileri ve mesaj geçmişi yerel SQLite veritabanında saklanır. Mesaj içeriği, Türkçe karakter setine göre düzenlenmiş 6x6 Playfair algoritmasıyla şifrelenir.

---

## 1. Projenin temel özellikleri

- Python 3 ile geliştirilmiştir.
- Windows 10/11, macOS ve Linux üzerinde çalışabilir.
- Arayüz için CustomTkinter kullanır.
- Ağ haberleşmesi için TCP socket kullanır.
- P2P yapıdadır; merkezi sunucu yoktur.
- Her bilgisayar kendi portunu dinler ve diğer bilgisayara IP adresiyle bağlanır.
- Kullanıcı parolaları düz metin olarak saklanmaz; SHA-256 hash olarak SQLite veritabanına kaydedilir.
- Gelen ve giden mesajlar yerel veritabanında tutulur.
- Karşı bilgisayarın giriş yaptığı kullanıcı adı sohbet ekranının üstünde görünür.
- Mesajlarda boşluk, nokta, virgül, soru işareti, ünlem ve iki nokta desteklenir.
- Varsayılan şifreleme anahtarı: `türkiyem!`

---

## 2. Proje dosya yapısı

```text
encrypted_p2p_chat/
│
├── run.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── app/
    ├── __init__.py
    ├── config.py
    │
    ├── crypto/
    │   ├── __init__.py
    │   └── playfair.py
    │
    ├── db/
    │   ├── __init__.py
    │   └── database.py
    │
    ├── network/
    │   ├── __init__.py
    │   └── peer.py
    │
    ├── ui/
    │   ├── __init__.py
    │   ├── login_window.py
    │   └── chat_window.py
    │
    └── utils/
        ├── __init__.py
        └── helpers.py
```

Kısa açıklama:

| Dosya/Klasör | Görevi |
|---|---|
| `run.py` | Uygulamayı başlatan ana dosyadır. |
| `requirements.txt` | Kurulması gereken Python paketlerini içerir. |
| `app/config.py` | Varsayılan port, varsayılan anahtar ve veritabanı yolu gibi ayarları tutar. |
| `app/crypto/playfair.py` | 6x6 Türkçe Playfair şifreleme ve çözme algoritmasını içerir. |
| `app/db/database.py` | SQLite veritabanı, kullanıcı kayıt/giriş ve mesaj geçmişi işlemlerini yapar. |
| `app/network/peer.py` | TCP/IP P2P bağlantı, dinleme, bağlanma, mesaj gönderme ve mesaj alma işlemlerini yapar. |
| `app/ui/login_window.py` | Kullanıcı kayıt/giriş ekranıdır. |
| `app/ui/chat_window.py` | Sohbet, bağlantı ve şifreleme arayüzüdür. |
| `app/utils/helpers.py` | Yerel IP bulma ve zaman bilgisi gibi yardımcı fonksiyonları içerir. |

---

## 3. 6x6 Türkçe Playfair karakter seti

Bu projede Playfair matrisi 36 hücrelidir.

29 Türkçe harf:

```text
a b c ç d e f g ğ h ı i j k l m n o ö p r s ş t u ü v y z
```

7 ek karakter:

```text
boşluk . , ? ! : ^
```

Toplam:

```text
29 harf + 7 ek karakter = 36 karakter
```

`^` karakteri teknik dolgu karakteridir. Playfair algoritmasında mesaj tek sayıda karakterden oluşursa veya aynı iki karakter yan yana gelirse araya dolgu karakteri eklenir.

Örnek desteklenen mesaj:

```text
merhaba dünya, nasılsın?
```

Bu mesaj boşluk ve noktalama işaretleri korunarak şifrelenir ve karşı tarafta yine okunabilir cümle olarak çözülür.

---

## 4. Kuruluma başlamadan önce

İki bilgisayarda da şunlar olmalıdır:

- Python 3.12
- İnternet bağlantısı, sadece kurulum sırasında paket indirmek için gerekir.
- İki bilgisayarın aynı Wi-Fi/LAN ağına bağlı olması gerekir.
- Windows tarafında güvenlik duvarı Python için ağ izni isteyebilir.

Önemli:

- İki bilgisayarda da aynı proje sürümünü kullanın.
- İki bilgisayarda da aynı şifreleme anahtarını kullanın.
- Varsayılan anahtar: `türkiyem!`
- Varsayılan port: `5050`

---

## 5. macOS kurulumu ve çalıştırma

Bu adımlar MacBook Silicon ve Intel Mac için kullanılabilir.

### 5.1. Homebrew kontrolü

Terminal açın ve şunu yazın:

```bash
brew --version
```

Sürüm bilgisi gelirse Homebrew kuruludur.

Eğer `command not found` gibi bir hata alırsanız Homebrew kurmanız gerekir. Homebrew kurulumu için Terminal'e şu komut yazılabilir:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Kurulum bittikten sonra Terminal'i kapatıp yeniden açın.

### 5.2. Python 3.12 ve Tkinter kurulumu

Mac üzerinde CustomTkinter çalışabilmesi için Python ile birlikte Tkinter desteği de gerekir.

```bash
brew install python@3.12
brew install python-tk@3.12
```

### 5.3. Proje klasörüne girme

ZIP dosyasını indirin ve çıkarın. Örneğin proje `Downloads` klasöründeyse:

```bash
cd ~/Downloads/encrypted_p2p_chat
```

Başka bir klasöre çıkardıysanız `cd` komutunda kendi klasör yolunuzu kullanın.

### 5.4. Sanal ortam oluşturma

```bash
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
```

Terminal satırının başında `(.venv)` yazıyorsa sanal ortam aktif demektir.

### 5.5. Gerekli paketleri kurma

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5.6. Tkinter test etme

```bash
python -m tkinter
```

Küçük bir test penceresi açılırsa Tkinter çalışıyor demektir. Pencereyi kapatabilirsiniz.

### 5.7. Uygulamayı çalıştırma

```bash
export TK_SILENCE_DEPRECATION=1
python run.py
```

Uygulama açıldıktan sonra Terminal'in beklemede kalması normaldir. Uygulama açık kaldığı sürece `python run.py` komutu çalışmaya devam eder.

---

## 6. Windows 10/11 kurulumu ve çalıştırma

### 6.1. Python kontrolü

PowerShell açın ve şunu yazın:

```powershell
python --version
```

veya:

```powershell
py --version
```

`Python 3.12.x` görüyorsanız Python kuruludur.

### 6.2. Tkinter kontrolü

PowerShell'de şunu çalıştırın:

```powershell
python -m tkinter
```

Küçük bir pencere açılırsa Tkinter vardır ve proje arayüzü çalışabilir.

Eğer bu komut hata verirse Microsoft Store Python yerine python.org üzerindeki resmi Python 3.12 kurulumunu kullanmanız önerilir. Kurulumda `Add python.exe to PATH` seçeneğini işaretleyin.

### 6.3. Proje klasörüne girme

ZIP dosyasını indirin ve çıkarın. Örneğin proje `Downloads` klasöründeyse:

```powershell
cd Downloads\encrypted_p2p_chat
```

Masaüstüne çıkardıysanız:

```powershell
cd Desktop\encrypted_p2p_chat
```

### 6.4. Sanal ortam oluşturma


```powershell
python -m venv .venv
```

### 6.5. Sanal ortamı aktif etme

```powershell
.\.venv\Scripts\Activate.ps1
```

Komut çalışınca satırın başında `(.venv)` görünür.

Eğer PowerShell script izni hatası verirse şu komutu bir kez çalıştırın:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Sonra tekrar sanal ortamı aktif edin:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 6.6. Gerekli paketleri kurma

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 6.7. Uygulamayı çalıştırma

```powershell
python run.py
```

Windows Güvenlik Duvarı izin isterse `Private networks / Özel ağlar` için izin verin.

---

## 7. İki bilgisayarda mesajlaşma testi

Aşağıdaki örnekte Mac ve Windows aynı Wi-Fi ağına bağlı kabul edilmiştir.

### 7.1. İki bilgisayarda da uygulamayı açın

Mac:

```bash
cd ~/Downloads/encrypted_p2p_chat
source .venv/bin/activate
python run.py
```

Windows:

```powershell
cd Downloads\encrypted_p2p_chat
.\.venv\Scripts\Activate.ps1
python run.py
```

### 7.2. Kullanıcı oluşturun

Her iki bilgisayarda da uygulama ilk açıldığında kullanıcı oluşturun.

Örnek:

Mac tarafı:

```text
Kullanıcı adı: ulas
Parola: 1234
```

Windows tarafı:

```text
Kullanıcı adı: kerem
Parola: 1234
```

Not: Kullanıcılar her bilgisayarın kendi SQLite veritabanına kaydedilir. Mac'te oluşturulan kullanıcı Windows'ta otomatik görünmez. Bu normaldir.

### 7.3. Giriş yapın

Oluşturduğunuz kullanıcı adı ve parola ile iki bilgisayarda da giriş yapın.

### 7.4. İki tarafta da dinlemeyi başlatın

Her iki bilgisayarda da `Dinlemeyi Başlat` düğmesine basın.

Varsayılan port:

```text
5050
```

### 7.5. IP adreslerini bulun

Uygulamanın sol tarafında `Yerel IP` alanı görünür.

Örnek:

```text
Mac Yerel IP: 192.168.1.34
Windows Yerel IP: 192.168.1.41
```

### 7.6. Bir bilgisayardan diğerine bağlanın

Mac'ten Windows'a bağlanmak için Mac uygulamasında şunları girin:

```text
Karşı Bilgisayar IP: 192.168.1.41
Karşı Port: 5050
```

Sonra `Bağlan` düğmesine basın.

Windows'tan Mac'e bağlanmak için Windows uygulamasında şunları girin:

```text
Karşı Bilgisayar IP: 192.168.1.34
Karşı Port: 5050
```

Sonra `Bağlan` düğmesine basın.

Sadece bir tarafın bağlanması yeterlidir. İki tarafın aynı anda birbirine bağlanması gerekmez.

### 7.7. Şifreleme anahtarını kontrol edin

İki tarafta da aynı anahtar yazılı olmalıdır.

Varsayılan:

```text
türkiyem!
```

Anahtar farklı olursa mesajlar doğru çözülemez.

### 7.8. Karşı kullanıcı adını kontrol edin

Bağlantı kurulduktan sonra sohbet ekranının üstünde şu alan görünür:

```text
Kiminle: karşı_kullanıcı_adı
```

Örneğin:

```text
Kiminle: kerem
```

### 7.9. Mesaj gönderin

Artık mesaj gönderebilirsiniz.

Örnek mesaj:

```text
merhaba dünya, nasılsın?
```

Bu mesaj karşı tarafa boşluk ve noktalama işaretleri korunarak gider.

---

## 8. Sık karşılaşılan sorunlar

### 8.1. Uygulama açılmıyor

Önce sanal ortamın aktif olduğundan emin olun.

Mac:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Sonra tekrar çalıştırın:

```bash
python run.py
```

### 8.2. `No module named customtkinter` hatası

Paketler kurulmamış demektir:

```bash
pip install -r requirements.txt
```

### 8.3. Mac'te `No module named _tkinter` hatası

Tkinter eksiktir:

```bash
brew install python-tk@3.12
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

### 8.4. Windows'ta pencere açılmıyor veya Tkinter hatası veriyor

Şunu test edin:

```powershell
python -m tkinter
```

Hata verirse python.org üzerinden Python 3.12 kurun ve kurulumda `Add python.exe to PATH` seçeneğini işaretleyin.

### 8.5. Bağlantı kurulamıyor

Şunları kontrol edin:

1. İki bilgisayar aynı Wi-Fi/LAN ağında mı?
2. İki tarafta da `Dinlemeyi Başlat` düğmesine basıldı mı?
3. IP adresi doğru yazıldı mı?
4. Port değeri iki tarafta da `5050` mi?
5. Windows Güvenlik Duvarı Python'a izin verdi mi?
6. Okul, yurt veya şirket ağı cihazlar arası bağlantıyı engelliyor olabilir mi?
7. Modemde `client isolation / AP isolation` ayarı açık olabilir mi?

### 8.6. Mesaj anlamsız çözülüyor

Bunun en yaygın nedeni iki tarafta şifreleme anahtarının farklı olmasıdır.

İki tarafta da anahtarı aynı yapın:

```text
türkiyem!
```

---

## 9. Sunumda kodu anlatmak için kısa özet

- `run.py` uygulamayı başlatır.
- `login_window.py` kullanıcı kayıt/giriş ekranını oluşturur.
- `database.py` kullanıcıları ve mesajları SQLite içinde saklar.
- Parolalar SHA-256 ile hashlenir; düz metin olarak tutulmaz.
- `chat_window.py` sohbet arayüzünü, bağlantı butonlarını ve mesaj gönderme/alma akışını yönetir.
- `peer.py` TCP soketleriyle P2P haberleşmeyi yürütür.
- Dinleme işlemi ayrı thread'de çalışır, bu yüzden arayüz donmaz.
- `playfair.py` mesajı 6x6 Türkçe Playfair algoritmasıyla şifreler ve çözer.
- İki bilgisayar aynı anahtarı kullanırsa mesaj doğru çözülür.
- Karşı taraf bağlantı kurunca uygulamalar birbirine `hello` paketi gönderir; böylece sohbet ekranında karşı kullanıcının adı görünür.

---

## 10. Projeyi kapatma

Uygulamayı pencerenin kapatma düğmesiyle kapatabilirsiniz.

Sanal ortamdan çıkmak isterseniz Terminal veya PowerShell'de şu komutu kullanın:

```bash
deactivate
```
