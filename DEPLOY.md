# نشر الموقع

## الخيار الأسهل: Render

1. ادخل <https://render.com> واربط حساب GitHub.
2. **New → Blueprint** واختار مستودع `hospital-booking`.
3. Render هيقرأ `render.yaml` وينشئ:
   - Web Service باسم `rady-hospital`
   - قاعدة PostgreSQL باسم `rady-db`
4. استنى الـ deploy يخلص، وافتح الرابط اللي هيظهر.

### بعد أول deploy

من **Shell** بتاع الخدمة:

```bash
python -m scripts.seed_rady
python -m scripts.create_admin
```

- `seed_rady` بيضيف الأقسام والدكاترة والمواعيد.
- `create_admin` بيسألك على بيانات الأدمن (الباسورد مخفي).

### ملاحظات

- الخطة المجانية بتنام بعد فترة خمول، وممكن قاعدة البيانات المجانية تنتهي.
  للاستخدام الحقيقي استخدم خطة مدفوعة.
- الدومين المخصص: **Settings → Custom Domain** ثم اتبع تعليمات DNS.
- HTTPS بيشتغل تلقائيًا على Render.

## الخيار الثاني: Docker على سيرفر

على أي سيرفر فيه Docker:

```bash
git clone https://github.com/mohamehk-77/hospital-booking.git
cd hospital-booking
cp .env.example .env
# عدّل POSTGRES_PASSWORD و SECRET_KEY في .env
docker compose up -d --build
```

وبعدها:

```bash
docker compose exec app python -m scripts.seed_rady
docker compose exec app python -m scripts.create_admin
```

الموقع على `http://SERVER_IP:8000`. يفضّل تحط Caddy أو Nginx قدامه
لدومين + HTTPS.

## قبل الاستخدام الحقيقي

- غيّر باسورد كل الدكاترة (الحالي `Doctor@12345`).
- غيّر باسورد الأدمن.
- `SECRET_KEY` قوي (Render بيولّد واحد تلقائيًا).
- `ENVIRONMENT=production` (بيقفل `/docs` و`/redoc`).
- باكاب دوري لقاعدة البيانات.
- راجع صلاحيات الحسابات التجريبية واحذف اللي مش محتاجه.

## نشر مجاني دائم على Oracle

راجع [DEPLOY-ORACLE.md](DEPLOY-ORACLE.md).
