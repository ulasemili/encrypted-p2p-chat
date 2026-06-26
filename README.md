# 🔐 Encrypted P2P Chat

Merkezi bir sunucu kullanmadan çalışan, güvenli ve şifreli eşler arası (Peer-to-Peer) haberleşme uygulaması.

Bu proje, ağ güvenliği ve kriptografi prensiplerini uygulamalı olarak göstermek amacıyla geliştirilmiştir. Kullanıcılar aynı ağ üzerinde veya farklı ağlarda doğrudan birbirleriyle bağlantı kurabilir, güvenli oturum anahtarı paylaşabilir ve mesajlarını şifreli şekilde iletebilirler.

Uygulama içerisinde kullanıcı yönetimi, sohbet geçmişi, güvenli anahtar paylaşımı, son konuşmalar ekranı, farklı ağ desteği ve ağ üzerinde taşınan verinin şifreli olduğunu gösterebilen Sniffer aracı bulunmaktadır.

---

# 🎯 Projenin Amacı

Geleneksel mesajlaşma uygulamalarında kullanıcılar genellikle merkezi bir sunucu üzerinden haberleşir.

Bu projede amaç:

* Merkezi sunucu kullanmamak
* Kullanıcıların doğrudan birbirleriyle haberleşmesini sağlamak
* Mesajların ağ üzerinde açık metin olarak gitmesini engellemek
* Güvenli anahtar paylaşımı gerçekleştirmek
* Şifreli haberleşmenin nasıl çalıştığını uygulamalı olarak göstermek

Bu nedenle sistem tamamen P2P (Peer-to-Peer) mantığıyla tasarlanmıştır.

---

# 🚀 Özellikler

### 👤 Kullanıcı Sistemi

* Kullanıcı kayıt olma
* Kullanıcı giriş yapma
* SHA-256 ile parola hashleme
* SQLite üzerinde güvenli kullanıcı saklama

---

### 🔑 Güvenli Oturum Anahtarı Paylaşımı

Bağlantıyı başlatan kullanıcı sohbet sırasında kullanılacak Playfair anahtarını belirler.

Bu anahtar:

* Ağ üzerinde düz metin olarak gönderilmez
* Diffie-Hellman (X25519) ile oluşturulan ortak gizli anahtar üzerinden korunur
* Fernet kullanılarak şifrelenir
* Karşı tarafa güvenli şekilde aktarılır

Bu sayede iki taraf aynı anahtara sahip olurken ağ üzerindeki bir saldırgan anahtarı elde edemez.

---

### 💬 Şifreli Mesajlaşma

Mesajlar gönderilmeden önce Playfair algoritması ile şifrelenir.

Gönderilen veri:

```text
MERHABA
```

yerine ağ üzerinde şu şekilde görünür:

```text
XZKJQMFV...
```

Alıcı taraf aynı oturum anahtarına sahip olduğu için mesajı çözebilir.

---

### 🖱 Mesaja Tıklayarak Açma

Mesajlar ilk olarak şifreli halde görüntülenir.

Kullanıcı isterse mesaj balonuna tıklayarak:

* Şifreli metni
* Açık metni

görüntüleyebilir.

Bu özellik özellikle proje sunumlarında şifreli veri akışını göstermek amacıyla eklenmiştir.

---

### 🌐 Aynı Wi-Fi Desteği

Kullanıcılar aynı yerel ağ üzerindeyse:

* Yerel IP adresi kullanarak
* Doğrudan bağlantı kurabilir

Örnek:

```text
192.168.1.25
```

---

### 🌍 Farklı Wi-Fi Desteği

Proje yalnızca yerel ağlarda değil farklı internet bağlantılarında da çalışabilir.

Bunun için Tailscale entegrasyonu kullanılmıştır.

Tailscale sayesinde:

* NAT problemleri ortadan kalkar
* Port yönlendirme gerekmez
* Cihazlar güvenli özel ağ içerisinde haberleşebilir

Uygulama içerisinde:

```text
Aynı Wi-Fi
```

ve

```text
Farklı Wi-Fi / Tailscale
```

olmak üzere iki farklı bağlantı modu bulunmaktadır.

---

### 🗂 Son Konuşmalar Sistemi

Kullanıcıların geçmiş konuşmaları yerel veritabanında tutulur.

Son konuşmalar ekranı sayesinde:

* Daha önce konuşulan kişiler görüntülenebilir
* Sohbet geçmişi tekrar açılabilir
* Sohbet geçmişi silinebilir
* Kullanıcı adı bazlı listeleme yapılır

---

### 🔒 Şifre Korumalı Geçmiş Erişimi

Sohbet geçmişine erişmek isteyen kullanıcıdan tekrar parola istenir.

Bu sayede:

* Bilgisayarı kullanan başka kişiler
* Açık kalan oturumlar

üzerinden geçmiş konuşmalar görüntülenemez.

---

### 🗑 Sohbet Geçmişi Silme

Son konuşmalar ekranında bulunan çöp kutusu simgesi sayesinde:

* İstenilen konuşma geçmişi
* Tek tıklamayla silinebilir

Silinen kayıtlar SQLite veritabanından kaldırılır.

---

### 🔍 Sniffer Proxy

Proje içerisinde bulunan Sniffer aracı eğitim ve sunum amaçlı geliştirilmiştir.

Bu araç sayesinde:

* Ağ üzerinden geçen paketler görüntülenebilir
* Mesajların düz metin gitmediği gösterilebilir
* Şifreli veri akışı analiz edilebilir

Sniffer yalnızca paketleri görüntüler.

Mesajları değiştirmez ve haberleşmeye müdahale etmez.

---

# 🏗 Sistem Mimarisi

Bağlantı süreci aşağıdaki şekilde çalışır:

```text
Kullanıcı A
      │
      │ Diffie-Hellman
      ▼
Ortak Gizli Anahtar
      │
      │ Fernet
      ▼
Playfair Anahtarının Güvenli Aktarımı
      │
      │
      ▼
Şifreli Haberleşme
      │
      ▼
Kullanıcı B
```

Mesaj gönderme süreci:

```text
Mesaj Yazılır
      │
      ▼
Playfair ile Şifrelenir
      │
      ▼
TCP/IP Üzerinden Gönderilir
      │
      ▼
Karşı Taraf Mesajı Alır
      │
      ▼
Playfair ile Çözer
      │
      ▼
Açık Metin Görüntülenir
```

---

# 🧰 Kullanılan Teknolojiler

| Teknoloji     | Kullanım Amacı                  |
| ------------- | ------------------------------- |
| Python 3      | Uygulama geliştirme             |
| CustomTkinter | Grafik arayüz                   |
| SQLite        | Kullanıcı ve mesaj kayıtları    |
| TCP Socket    | P2P haberleşme                  |
| Threading     | Eş zamanlı veri alma            |
| SHA-256       | Parola hashleme                 |
| X25519        | Diffie-Hellman anahtar değişimi |
| Fernet        | Güvenli anahtar aktarımı        |
| Playfair 6x6  | Mesaj şifreleme                 |
| Tailscale     | Farklı ağlarda bağlantı         |
| Sniffer Proxy | Trafik analizi                  |

```
```
# 📥 Kurulum

Uygulamayı çalıştırabilmek için bilgisayarınızda Python kurulu olmalıdır.

Desteklenen işletim sistemleri:

* Windows
* macOS
* Linux

---

# 🖥 Windows Kurulumu

## 1. Python Kurulumu

Öncelikle Python 3.12 veya daha güncel bir sürüm kurulu olmalıdır.

Kurulum sırasında aşağıdaki seçeneğin işaretli olduğundan emin olun:

```text
Add Python to PATH
```

Kurulum tamamlandıktan sonra Komut İstemi'ni açın ve aşağıdaki komutu çalıştırın:

```powershell
python --version
```

Örnek çıktı:

```text
Python 3.12.4
```

---

## 2. Projeyi İndirme

Git kullanıyorsanız:

```powershell
git clone https://github.com/USERNAME/encrypted-p2p-chat.git
cd encrypted-p2p-chat
```

Git kullanmıyorsanız GitHub üzerinden ZIP indirip klasöre çıkartabilirsiniz.

---

## 3. Sanal Ortam Oluşturma

```powershell
python -m venv .venv
```

---

## 4. Sanal Ortamı Aktifleştirme

```powershell
.\.venv\Scripts\Activate.ps1
```

Başarılı olursa terminal satırının başında aşağıdakine benzer bir ifade görünür:

```text
(.venv)
```

---

## 5. Gerekli Paketleri Kurma

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 6. Uygulamayı Başlatma

```powershell
python run.py
```

---

# 🍎 macOS Kurulumu

## 1. Homebrew Kurulumu

Homebrew kurulu değilse:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

---

## 2. Python Kurulumu

```bash
brew install python@3.12
```

---

## 3. Projeyi İndirme

```bash
git clone https://github.com/USERNAME/encrypted-p2p-chat.git
cd encrypted-p2p-chat
```

---

## 4. Sanal Ortam Oluşturma

```bash
python3 -m venv .venv
```

---

## 5. Sanal Ortamı Aktifleştirme

```bash
source .venv/bin/activate
```

---

## 6. Paketleri Kurma

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 7. Uygulamayı Çalıştırma

```bash
python run.py
```

---

# 🚀 İlk Kullanım

Uygulama açıldığında giriş ekranı görüntülenir.

İlk kullanımda:

1. Kullanıcı adı belirleyin.
2. Şifre belirleyin.
3. Kayıt Ol seçeneğini kullanın.
4. Daha sonra aynı bilgilerle giriş yapın.

Parolalar düz metin olarak saklanmaz.

Kullanıcı parolaları SHA-256 algoritması kullanılarak hashlenir ve veritabanında güvenli şekilde tutulur.

---

# 🔗 Aynı Wi-Fi Ağında Bağlantı Kurma

Bu yöntem iki cihaz aynı ağ üzerindeyken kullanılır.

Örneğin:

```text
Bilgisayar A → 192.168.1.20
Bilgisayar B → 192.168.1.35
```

---

## Adım 1

İki bilgisayarda da uygulamayı açın.

---

## Adım 2

İki bilgisayarda da giriş yapın.

---

## Adım 3

İki bilgisayarda da:

```text
Dinlemeyi Başlat
```

butonuna basın.

---

## Adım 4

Bağlantıyı başlatacak kullanıcı:

```text
Aynı Wi-Fi
```

modunu seçer.

---

## Adım 5

Karşı bilgisayarın IP adresini girer.

Örnek:

```text
192.168.1.35
```

---

## Adım 6

Mesajlaşmada kullanılacak Playfair anahtarını belirler.

Örnek:

```text
gizli_anahtar
```

---

## Adım 7

Bağlan butonuna basar.

---

## Adım 8

Bağlantı tamamlandıktan sonra güvenli oturum oluşturulur ve mesajlaşma başlayabilir.

---

# 🌍 Farklı Wi-Fi Ağlarında Kullanım

Bu özellik sayesinde kullanıcılar farklı şehirlerde, farklı evlerde veya farklı internet bağlantılarında olsalar bile haberleşebilir.

Bu işlem için Tailscale kullanılmaktadır.

---

# 🛡 Tailscale Kurulumu

Windows:

https://tailscale.com/download/windows

macOS:

https://tailscale.com/download

Kurulum tamamlandıktan sonra aynı hesap ile giriş yapılmalıdır.

---

# Tailscale IP Öğrenme

Terminal açın:

```bash
tailscale ip -4
```

Örnek çıktı:

```text
100.124.216.57
```

Bu IP adresi uygulamada kullanılacaktır.

---

# Farklı Ağlarda Bağlantı Kurma

Dinleyen cihaz:

```text
Dinlemeyi Başlat
```

butonuna basar.

Bağlanan cihaz:

```text
Farklı Wi-Fi / Tailscale
```

modunu seçer.

Karşı cihazın Tailscale IP adresini girer.

Örnek:

```text
100.124.216.57
```

Bağlan butonuna basar.

Bağlantı kurulduktan sonra normal şekilde mesajlaşılabilir.

---

# 🗂 Son Konuşmalar

Uygulama konuşmaları otomatik olarak kaydeder.

Sol tarafta bulunan:

```text
Son Konuşmalar
```

alanı sayesinde daha önce iletişim kurulan kullanıcılar görüntülenebilir.

---

## Sohbet Geçmişini Açma

Bir konuşmaya tıklandığında kullanıcıdan şifre istenir.

Şifre doğrulandıktan sonra geçmiş mesajlar yüklenir.

Bu özellik cihaz başında bulunan farklı kişilerin sohbet geçmişlerini görüntülemesini engellemek amacıyla eklenmiştir.

---

## Sohbet Geçmişini Silme

Her konuşmanın yanında çöp kutusu simgesi bulunur.

Bu simgeye basıldığında:

* İlgili konuşma
* Mesaj kayıtları
* Sohbet geçmişi

veritabanından kaldırılır.

---

# 🔍 Sniffer GUI

Proje içerisinde bulunan Sniffer aracı eğitim amaçlı geliştirilmiştir.

Amaç ağ üzerinde taşınan verinin gerçekten şifreli olduğunu göstermektir.

---

# Sniffer Başlatma

```bash
python -m app.tools.sniffer_gui
```

---

# Sniffer Nasıl Çalışır?

Normal haberleşme:

```text
Gönderici
     │
     ▼
Alıcı
```

Sniffer kullanıldığında:

```text
Gönderici
     │
     ▼
Sniffer
     │
     ▼
Alıcı
```

---

# Sniffer Kullanımı

Dinleme Portu:

```text
6060
```

Gerçek Alıcı Portu:

```text
5050
```

Gönderici cihaz:

```text
Karşı IP = Sniffer IP
Karşı Port = 6060
```

şeklinde bağlanır.

---

# Sniffer Ne Gösterir?

Sniffer mesajların düz metin halini göstermez.

Örneğin kullanıcı:

```text
Merhaba
```

gönderdiğinde Sniffer ekranında:

```text
QJXKZBVP...
```

gibi şifreli veri görülür.

Bu durum sistemin gerçekten şifreli haberleştiğini gösterir.

---

# 📁 Proje Yapısı

```text
encrypted-p2p-chat
│
├── run.py
├── requirements.txt
├── README.md
│
└── app
    │
    ├── crypto
    │   ├── playfair.py
    │   └── key_exchange.py
    │
    ├── db
    │   └── database.py
    │
    ├── network
    │   └── peer.py
    │
    ├── ui
    │   ├── login_window.py
    │   └── chat_window.py
    │
    ├── tools
    │   ├── sniffer_proxy.py
    │   └── sniffer_gui.py
    │
    └── utils
        └── helpers.py
```

---

# 🧪 Akademik Amaç

Bu proje;

* Kriptografi
* Ağ Programlama
* Güvenli Haberleşme
* P2P Sistemler
* Anahtar Yönetimi
* Trafik Analizi

konularını uygulamalı olarak göstermek amacıyla geliştirilmiştir.

---

# ⚠️ Not

Bu proje eğitim ve akademik çalışmalar için geliştirilmiştir.

Gerçek dünyadaki ticari mesajlaşma uygulamalarında:

* Kimlik doğrulama
* Sertifika yönetimi
* İleri seviye anahtar rotasyonu
* Güvenlik denetimleri

gibi ek mekanizmalar kullanılmaktadır.
