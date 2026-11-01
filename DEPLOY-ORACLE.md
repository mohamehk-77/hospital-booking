# نشر دائم مجاني: Oracle Cloud + DuckDNS + Caddy

الحل ده بيشغّل الموقع 24/7 على سيرفر مجاني من Oracle، مع دومين مجاني من
DuckDNS وشهادة HTTPS تلقائية من Caddy.

## 1) حساب Oracle

1. افتح <https://www.oracle.com/cloud/free/> واعمل حساب.
2. محتاج كارت للتحقق (مش هيتخصم منه حاجة لو فضلت داخل الحدود المجانية).
3. اختار Home Region قريب من مصر (مثلاً Frankfurt أو Amsterdam).

## 2) إنشاء السيرفر

من **Compute → Instances → Create instance**:

- **Image:** Ubuntu 24.04
- **Shape:** Ampere → `VM.Standard.A1.Flex`
  - 2 OCPU و 12 GB كفاية (الحد المجاني 4 OCPU / 24 GB).
- **Networking:** Assign a public IPv4 address.
- **SSH keys:** نزّل المفتاح الخاص (`.key`) واحتفظ بيه.
- **Boot volume:** 50–100 GB.

## 3) افتح البورتات

من **VCN → Security Lists → Default Security List** أضف Ingress Rules:

| Source | Protocol | Port |
|---|---|---|
| 0.0.0.0/0 | TCP | 80 |
| 0.0.0.0/0 | TCP | 443 |

سيب بورت 22 مفتوح للـ SSH.

> لو بتستخدم Network Security Group، ضيف القواعد هناك كمان.
> القواعد دي غير كافية لوحدها — سكربت التثبيت بيظبط UFW جوه السيرفر.

## 4) DuckDNS

1. افتح <https://www.duckdns.org> وسجّل دخول بـ GitHub/Google.
2. في **add domain** اكتب: `radyhospital` → **add domain**.
3. في خانة `current ip` حط **Public IP** بتاع سيرفر Oracle → **update ip**.
4. تأكد من الجهاز:

```powershell
nslookup radyhospital.duckdns.org
```

لازم يرجّع IP السيرفر.

5. سجّل الـ **token** اللي ظاهر فوق (مش هتحتاجه لو IP ثابت).

## 5) تثبيت الموقع

اتصل بالسيرفر:

```bash
chmod 600 ssh-key.key
ssh -i ssh-key.key ubuntu@PUBLIC_IP
```

على السيرفر:

```bash
sudo apt-get update
sudo apt-get install -y git
git clone https://github.com/mohamehk-77/hospital-booking.git
cd hospital-booking
bash deploy/oracle-setup.sh
```

السكربت بيسألك على الدومين:

```
radyhospital.duckdns.org
```

وهيولّد `SECRET_KEY` و`POSTGRES_PASSWORD` تلقائيًا، ويشغّل:
- PostgreSQL
- التطبيق
- Caddy على 80/443

## 6) إنشاء الأدمن

```bash
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml exec app python -m scripts.create_admin
```

## 7) افتح الموقع

```
https://radyhospital.duckdns.org
```

أول شهادة HTTPS ممكن تاخد دقيقة. تابع اللوج:

```bash
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f caddy
```

## 8) التحديثات

```bash
cd ~/hospital-booking
git pull
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

## 9) باكاب

```bash
sudo docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T db \
  pg_dump -U postgres hospital_db > backup-$(date +%F).sql
```

حط الأمر في cron يومي، وانقل النسخ لمكان تاني.

## 10) تحديث DuckDNS لو IP اتغير

Oracle بيدّيك IP ثابت طول ما السيرفر شغال. لو حصل تغيير:

```bash
curl "https://www.duckdns.org/update?domains=radyhospital&token=YOUR_TOKEN&ip="
```

أو أضف cron كل 5 دقائق:

```bash
(crontab -l 2>/dev/null; echo "*/5 * * * * curl -s 'https://www.duckdns.org/update?domains=radyhospital&token=YOUR_TOKEN&ip=' >/dev/null") | crontab -
```

## ملاحظات أمان

- `ENVIRONMENT=production` بيقفل `/docs` و`/redoc`.
- غيّر باسورد الدكاترة (`Doctor@12345`) والأدمن.
- `.env.prod` فيه أسرار — متعملهوش commit.
- خلي بورت 22 مفتوح من IPك بس لو ممكن.
- اعمل باكاب دوري.
