import requests
import json

raw_email = """Delivered-To: ravinfredico1005@gmail.com
Received: by 2002:a05:6e16:907:b0:427:edd:bffd with SMTP id ru7csp3556901ysc;
        Wed, 4 Feb 2026 18:37:52 -0800 (PST)
X-Received: by 2002:a05:6a21:4508:b0:38b:ecae:6713 with SMTP id adf61e73a8af0-393720cd6a8mr4748738637.19.1770259071963;
        Wed, 04 Feb 2026 18:37:51 -0800 (PST)
ARC-Seal: i=1; a=rsa-sha256; t=1770259071; cv=none;
        d=google.com; s=arc-20240605;
        b=HCr4/ji9/v4Mtbnu09uKjz04J+Q7b1uzoIXIU6Zj2W0t2kaDVArAmdmaY6mBaFClfg
         FuH7tj9TSHu6Oj17s0vWu5vYi/I9r9bN7xthfEAoQAOw0gtf0ge7Qzh5bzKa/LzicgUk
         ZhekeMXKzjG3cdXRGNk2VDaKKwQPjQN9gx6RHQCH6zMxUn7F6I8P0pZ7In0C4hAddC6L
         ST5LI8qod8nC2TsXp0NLbgZAbevoXRLe7yyoPGHYn0OUGZ2GUxrP52MHwHc/sWhpIq5N
         jjPDCDOpE3AFwqyvD8Zr0c0BTx0G7I/vdMjATv/StxwlXkca5VlRTbcvXyrtW/jOfQ0L
         t3eQ==
ARC-Message-Signature: i=1; a=rsa-sha256; c=relaxed/relaxed; d=google.com; s=arc-20240605;
        h=feedback-id:mime-version:date:content-transfer-encoding:importance
         :message-id:subject:to:from:dkim-signature:dkim-signature;
        bh=QelrVw0wk1HRpnFjbAV/Jkm3mbFA1RnHNNMlrtaxGJA=;
        fh=mh3R+ZeWCLL6obNlAuDUGpIjEOVajQJWcTuy0W2amVo=;
        b=b5RpkUspGrlX8eKHB5g88DhwaVI92VcVjxysCH98RHbyCCv0Jr0KOg8MAsNmkca4yw
         TNSseAwvnmM8DwtcNwHX2CoIoXl/zjIcm88EzsvM+NoKU/dfaxLC9H16KcTGr5mU0U5y
         Yj6s0SbAQPKrZ3fpNcMep3ZX9ASlRtrY1CiKM0a1Smh90xJEo646sVtsnJQ8E0hA6ZxU
         1jmY09ppSD5mjaBjPcBhyPat5PM5zwb+JaJ16gxli1Q9C6q/QGPjLp2c6Mi3gF/YdSrC
         JKqc+cZ1dqqRGiilO1d+sPUeTtvwKZ7ihxnRbvuZHzqKLCtPSJGXJHuGYa0VwLVV2Wcy
         KU7A==;
        dara=google.com
ARC-Authentication-Results: i=1; mx.google.com;
       dkim=pass header.i=@notification.dealls.com header.s=jb4mdr2u2yv66wj4yzxaezyhd7m7jv34 header.b=OWBo58F6;
       dkim=pass header.i=@amazonses.com header.s=pd64dbxfdcqqbvadj6zks7h7qe3c33ao header.b=WR6gDN+9;
       spf=pass (google.com: domain of 010e019c2ba9c058-472b59c4-ce0c-4e41-8b6d-cc94ee817883-000000@ap-southeast-1.amazonses.com designates 23.251.232.55 as permitted sender) smtp.mailfrom=010e019c2ba9c058-472b59c4-ce0c-4e41-8b6d-cc94ee817883-000000@ap-southeast-1.amazonses.com;
       dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) header.from=notification.dealls.com
Return-Path: <010e019c2ba9c058-472b59c4-ce0c-4e41-8b6d-cc94ee817883-000000@ap-southeast-1.amazonses.com>
Received: from e232-55.smtp-out.ap-southeast-1.amazonses.com (e232-55.smtp-out.ap-southeast-1.amazonses.com. [23.251.232.55])
        by mx.google.com with ESMTPS id 41be03b00d2f7-c6c86cb8453si5498765a12.405.2026.02.04.18.37.51
        for <ravinfredico1005@gmail.com>
        (version=TLS1_3 cipher=TLS_AES_128_GCM_SHA256 bits=128/128);
        Wed, 04 Feb 2026 18:37:51 -0800 (PST)
Received-SPF: pass (google.com: domain of 010e019c2ba9c058-472b59c4-ce0c-4e41-8b6d-cc94ee817883-000000@ap-southeast-1.amazonses.com designates 23.251.232.55 as permitted sender) client-ip=23.251.232.55;
Authentication-Results: mx.google.com;
       dkim=pass header.i=@notification.dealls.com header.s=jb4mdr2u2yv66wj4yzxaezyhd7m7jv34 header.b=OWBo58F6;
       dkim=pass header.i=@amazonses.com header.s=pd64dbxfdcqqbvadj6zks7h7qe3c33ao header.b=WR6gDN+9;
       spf=pass (google.com: domain of 010e019c2ba9c058-472b59c4-ce0c-4e41-8b6d-cc94ee817883-000000@ap-southeast-1.amazonses.com designates 23.251.232.55 as permitted sender) smtp.mailfrom=010e019c2ba9c058-472b59c4-ce0c-4e41-8b6d-cc94ee817883-000000@ap-southeast-1.amazonses.com;
       dmarc=pass (p=QUARANTINE sp=QUARANTINE dis=NONE) header.from=notification.dealls.com
DKIM-Signature: v=1; a=rsa-sha256; q=dns/txt; c=relaxed/simple; s=jb4mdr2u2yv66wj4yzxaezyhd7m7jv34; d=notification.dealls.com; t=1770259071; h=Content-Type:From:To:Subject:Message-ID:Content-Transfer-Encoding:Date:MIME-Version; bh=aNMI8m4WCgx9IDXfZIOjSwlV7H73AnhADxGqd3JUiic=; b=OWBo58F6HP7Kgb8y0z4UV/o1Mp6vwGZ6gPfbXO9X5ZVsxt3B+MXlylp/HT59slNC ypI1KkIbKkNQZRxJxPDSX82gRPstZLdknc57DZG2wWRzGJcMSo4A1Lav8dUrm/elvI8 GWdk9UmJmySUsIO24yBxoAlENHm56axdnR3mpXWyGLqIJisQ5c7cp38d7j0tZh8rEO5 mGS3eHeWF58s15nQ5kWGCYXs8bcTK14/Gjo/abVOZRxQZ3DV4IK16yM9HVfjMwzqV0P t6RyRQ6z01yp6HYyyWbhSZqqvFidPS3ImapxZKVE6/OopLnY4rT7S+zRKHnsZompnJn wZrww5QKDQ==
DKIM-Signature: v=1; a=rsa-sha256; q=dns/txt; c=relaxed/simple; s=pd64dbxfdcqqbvadj6zks7h7qe3c33ao; d=amazonses.com; t=1770259071; h=Content-Type:From:To:Subject:Message-ID:Content-Transfer-Encoding:Date:MIME-Version:Feedback-ID; bh=aNMI8m4WCgx9IDXfZIOjSwlV7H73AnhADxGqd3JUiic=; b=WR6gDN+9ZwRKaXY/HnJs1DLQAlhsnxq5rH/i70cWVhY7pZ/bp1aRq7FE9BjC9Fi5 xaLPT+XjLgCseNMn/w4RoYz2CbUpsMXclQuFj/As1zOeDhoDqBL8Sb5xDpdJD2i47nu YA7b8t0DNNCQAY045HdnqN0tWGXGw9ZIaacQowIQ=
Content-Type: text/html; charset=utf-8
From: Ivana from Dealls <ivana@notification.dealls.com>
To: ravinfredico1005@gmail.com
Subject: Verify your Deall Account to Get Exclusive Job Offers 🤝
Message-ID: <010e019c2ba9c058-472b59c4-ce0c-4e41-8b6d-cc94ee817883-000000@ap-southeast-1.amazonses.com>
X-Priority: 1 (Highest)
X-Msmail-Priority: High
Importance: High
Content-Transfer-Encoding: quoted-printable
Date: Thu, 5 Feb 2026 02:37:51 +0000
MIME-Version: 1.0
Feedback-ID: ::1.ap-southeast-1.MEyT8ZxLKBkCtrQfehaQ0Q7MaGrBI9496zl1EULNdrc=:AmazonSES
X-SES-Outgoing: 2026.02.05-23.251.232.55

<!DOCTYPE html>
<html lang=3D"en">
=09<head>
=09=09<meta charset=3D"UTF-8" />
=09=09<meta http-equiv=3D"X-UA-Compatible" content=3D"IE=3Dedge" />
=09=09<meta name=3D"viewport" content=3D"width=3Ddevice-width, initial-scal=
e=3D1.0" />
=09=09<title>Email</title>

=09=09<style>
=09=09=09p {
=09=09=09=09margin: 0;
=09=09=09=09padding: 0;
=09=09=09}

=09=09=09ul {
=09=09=09=09margin: 0;
=09=09=09}

=09=09=09.container {
=09=09=09=09max-width: 711px;
=09=09=09=09width: 100%;
=09=09=09=09border-radius: 16px;
=09=09=09}

=09=09=09.header {
=09=09=09=09font-size: 28px;
=09=09=09}

=09=09=09.header-container {
=09=09=09=09margin-bottom: 44px;
=09=09=09}

=09=09=09.body {
=09=09=09=09font-size: 16px;
=09=09=09=09color: #313131;
=09=09=09=09line-height: 130%;
=09=09=09}

=09=09=09.wrapper {
=09=09=09=09padding: 33px;
=09=09=09}

=09=09=09.cta-button {
=09=09=09=09margin: 35px auto 35px auto;
=09=09=09=09display: block;
=09=09=09=09font-size: 22px;
=09=09=09=09padding: 17px 50px;
=09=09=09=09line-height: 22px;
=09=09=09}

=09=09=09.tips-section {
=09=09=09=09padding: 21px 33px 66px 33px;
=09=09=09}

=09=09=09.tips-header {
=09=09=09=09color: #484848;
=09=09=09=09line-height: 65px;
=09=09=09=09font-size: 28px;
=09=09=09=09font-weight: 700;
=09=09=09}

=09=09=09.tips-content {
=09=09=09=09color: #5f5f5f;
=09=09=09=09font-size: 22px;
=09=09=09=09line-height: 150%;
=09=09=09}

=09=09=09.footer {
=09=09=09=09font-size: 13px;
=09=09=09=09width: 76%;
=09=09=09}

=09=09=09.student-name {
=09=09=09=09font-size: 16px;
=09=09=09=09color: #313131;
=09=09=09=09font-weight: 700;
=09=09=09}

=09=09=09.student-header {
=09=09=09=09font-size: 12px;
=09=09=09=09color: #313131;
=09=09=09=09font-weight: 600;
=09=09=09}

=09=09=09.info-section-title {
=09=09=09=09background-color: #f4f2ff;
=09=09=09=09padding: 12px 20px;
=09=09=09=09color: #4b0a9e;
=09=09=09=09font-size: 16px;
=09=09=09=09font-weight: 700;
=09=09=09=09border-left: 7px solid #6014c3;
=09=09=09}

=09=09=09.cta-table {
=09=09=09=09display: block;
=09=09=09}

=09=09=09.cta-table-mobile {
=09=09=09=09display: none;
=09=09=09}

=09=09=09@media only screen and (max-width: 768px) {
=09=09=09=09.container {
=09=09=09=09=09max-width: 544px;
=09=09=09=09=09margin: 0 auto;
=09=09=09=09=09width: 100%;
=09=09=09=09=09border-radius: 8px;
=09=09=09=09}

=09=09=09=09.cta-table {
=09=09=09=09=09display: none;
=09=09=09=09}

=09=09=09=09.cta-table-mobile {
=09=09=09=09=09display: table;
=09=09=09=09}

=09=09=09=09.header {
=09=09=09=09=09font-size: 28px;
=09=09=09=09=09line-height: 34px;
=09=09=09=09}

=09=09=09=09.header-container {
=09=09=09=09=09margin-bottom: 36px;
=09=09=09=09}

=09=09=09=09.wrapper {
=09=09=09=09=09padding: 33px;
=09=09=09=09}

=09=09=09=09.body,
=09=09=09=09.footer,
=09=09=09=09.greeting-section {
=09=09=09=09=09font-size: 13px;
=09=09=09=09=09line-height: 24px;
=09=09=09=09=09width: 100%;
=09=09=09=09}

=09=09=09=09.footer {
=09=09=09=09=09width: 95%;
=09=09=09=09}

=09=09=09=09.cta-button {
=09=09=09=09=09font-size: 16px;
=09=09=09=09=09padding: 7px 25px;
=09=09=09=09=09line-height: 16px;
=09=09=09=09=09margin: 20px auto 25px auto;
=09=09=09=09}

=09=09=09=09.tips-section {
=09=09=09=09=09padding: 17px 33px 42px 33px;
=09=09=09=09}

=09=09=09=09.body,
=09=09=09=09.tips-content,
=09=09=09=09.greeting-section,
=09=09=09=09.tips-section {
=09=09=09=09=09font-size: 16px;
=09=09=09=09=09line-height: 24px;
=09=09=09=09}

=09=09=09=09.tips-header {
=09=09=09=09=09font-size: 20px;
=09=09=09=09=09line-height: 24px;
=09=09=09=09}
=09=09=09}

=09=09=09@media only screen and (max-width: 426px) {
=09=09=09=09.wrapper {
=09=09=09=09=09padding: 32px 24px 24px 24px;
=09=09=09=09}

=09=09=09=09.tips-section {
=09=09=09=09=09padding: 17px 24px 24px 32px;
=09=09=09=09}
=09=09=09}
=09=09</style>
=09</head>

=09<body style=3D"padding: 0; margin: 0">
=09=09<table
=09=09=09style=3D"
=09=09=09=09table-layout: fixed;
=09=09=09=09background-color: #faf8ff;
=09=09=09=09width: 100%;
=09=09=09=09margin: auto;
=09=09=09=09padding-bottom: 66px;
=09=09=09=09@import url('https://fonts.googleapis.com/css2?family=3DInter:w=
ght@300;400&display=3Dswap');
=09=09=09=09font-family: inter, arial;
=09=09=09"
=09=09>
=09=09=09<!--change this background url  -->
=09=09=09<tbody
=09=09=09=09style=3D"
=09=09=09=09=09background-image: url('https://cdn.sejutacita.id/assets/emai=
l/f8e947a8d7c8bb132bffce7b89d25d20/assets/bg-rect.png?raw=3Dtrue');
=09=09=09=09=09background-size: 300px;
=09=09=09=09=09background-repeat: no-repeat;
=09=09=09=09"
=09=09=09>
=09=09=09=09<tr>
=09=09=09=09=09<td align=3D"center">
=09=09=09=09=09=09<div>
=09=09=09=09=09=09=09<table
=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09max-width: 711px;
=09=09=09=09=09=09=09=09=09margin-right: auto;
=09=09=09=09=09=09=09=09=09margin-left: auto;
=09=09=09=09=09=09=09=09=09width: 100% !important;
=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09<tr>
=09=09=09=09=09=09=09=09=09<td>
=09=09=09=09=09=09=09=09=09=09<div
=09=09=09=09=09=09=09=09=09=09=09class=3D"header"
=09=09=09=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09=09=09=09display: block;
=09=09=09=09=09=09=09=09=09=09=09=09text-align: center;
=09=09=09=09=09=09=09=09=09=09=09=09padding: 20px 0;
=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09<!--change this img url  -->
=09=09=09=09=09=09=09=09=09=09=09<img
=09=09=09=09=09=09=09=09=09=09=09=09src=3D"https://yeppye.stripocdn.email/c=
ontent/guids/CABINET_a60cd4386590c5b6d34d8a89c0e5207dd97653e3e9d2eac3884326=
7cdff9ee73/images/01_logo_web_no_bg_1_1.png?raw=3Dtrue"
=09=09=09=09=09=09=09=09=09=09=09=09alt=3D""
=09=09=09=09=09=09=09=09=09=09=09/>
=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09<div
=09=09=09=09=09=09=09=09=09=09=09class=3D"content__wrapper"
=09=09=09=09=09=09=09=09=09=09=09style=3D"width: 100%; margin: 37px auto 33=
px auto"
=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09<div
=09=09=09=09=09=09=09=09=09=09=09=09class=3D"content container"
=09=09=09=09=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09=09=09=09=09background-color: #fff;
=09=09=09=09=09=09=09=09=09=09=09=09=09box-shadow: 0px 0px 14px 0px rgba(21=
9, 219, 219, 1);
=09=09=09=09=09=09=09=09=09=09=09=09=09line-height: 1.5rem;
=09=09=09=09=09=09=09=09=09=09=09=09=09word-wrap: break-word;
=09=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09<div class=3D"wrapper">
=09=09=09=09=09=09=09=09=09=09=09=09=09<div class=3D"header-container">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09font-weight: 700;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09display: inline;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09color: #313131;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09class=3D"header"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09Welcome
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<!-- change this background-ur=
l -->
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<span
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09class=3D"user-name"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09background-image: url('h=
ttps://cdn.sejutacita.id/assets/email/f8e947a8d7c8bb132bffce7b89d25d20/asse=
ts/name-line.png?raw=3Dtrue');
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09background-repeat: no-re=
peat;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09background-position: lef=
t bottom;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09padding-bottom: 10px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09background-size: fit;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>Ravin Fredico</span
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<!-- use first name -->
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<span>!</span>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09=09=09</div>

=09=09=09=09=09=09=09=09=09=09=09=09=09<div class=3D"body">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09<p>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09Dealls is committed to make yo=
ur job-seeking easier
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09than ever. We will connect you=
r profile to 450+
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09top companies so you can recei=
ve exclusive
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09invitations to exciting jobs d=
irectly in your
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09inbox.
=09=09=09=09=09=09=09=09=09=09=09=09=09=09</p>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09<br />
=09=09=09=09=09=09=09=09=09=09=09=09=09=09<p>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09To ensure you=E2=80=99ll recei=
ve future offers and
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09invitations, let=E2=80=99s ver=
ify and secure your email
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09address =E2=88=92 it takes one=
 click only! =F0=9F=91=87
=09=09=09=09=09=09=09=09=09=09=09=09=09=09</p>

=09=09=09=09=09=09=09=09=09=09=09=09=09=09<table
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09class=3D"cta-table"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09table-layout: fixed;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09width: 100%;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09margin-top: 16px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09padding: 0 10px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09padding-top: 4px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09border-radius: 8px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09border: 1px solid #c4=
bdf3;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<table
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09table-layout: fixe=
d;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09width: 100%;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09border-collapse: c=
ollapse;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<table>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<img
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09sty=
le=3D"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=
border-radius: 50%;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=
min-width: 56px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=
min-height: 56px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=
max-width: 56px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=
max-height: 56px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09src=
=3D"https://cdn.sejutacita.id/assets/email/avatar.png"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09/>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div s=
tyle=3D"margin-left: 10px">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<di=
v class=3D"student-name">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=
<span>Ravin Fredico</span>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</d=
iv>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</table>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>

=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09vertical-ali=
gn: middle;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09white-space:=
 nowrap;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09width: 220px=
;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<a
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09padding: =
12px 24px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09margin: 0=
;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09font-size=
: 16px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09color: wh=
ite;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09backgroun=
d-color: #6014c3;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09border-ra=
dius: 100px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09font-weig=
ht: 700;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09text-deco=
ration: none;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09float: ri=
ght;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09href=3D"http=
s://dealls.com"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>Verify Acco=
unt</a
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</table>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09</table>

=09=09=09=09=09=09=09=09=09=09=09=09=09=09<table
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09class=3D"cta-table-mobile"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09table-layout: fixed;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09width: 100%;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09border-spacing: 10px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09margin: 24px auto;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09border-radius: 8px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09border: 1px solid #c4bdf3;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<tr style=3D"width: 100% !impo=
rtant">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<table>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<img
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09border-ra=
dius: 50%;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09min-width=
: 62px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09min-heigh=
t: 62px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09max-width=
: 62px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09max-heigh=
t: 62px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09src=3D"https=
://cdn.sejutacita.id/assets/email/avatar.png"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09/>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div style=3D"m=
argin-left: 10px">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div class=
=3D"student-name">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<span>Rav=
in Fredico</span>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<p class=3D"=
student-header">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</p>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</table>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td style=3D"vertical-align=
: middle">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<a
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09href=3D"https://deall=
s.com"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"text-decorat=
ion: none"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09width: 90%;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09text-align: cen=
ter;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09padding: 12px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09margin: 0 auto;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09line-height: 20=
px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09font-size: 14px=
;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09color: white;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09background-colo=
r: #6014c3;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09border-radius: =
100px;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09font-weight: 70=
0;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09white-space: no=
wrap;
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09Verify Account
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</a>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09</table>

=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09class=3D"greeting-section"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"margin-top: 16px"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div class=3D"regards">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<p>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09Cheers,
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<br />
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<strong style=3D"color: =
#767676"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>Dealls Team =F0=9F=
=92=9C</strong
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</p>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>

=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09class=3D"info-section-title"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"margin-top: 18px"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09Why is this step important?
=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>

=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div style=3D"margin-top: 24px">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<table style=3D"border-spacing=
: 8px">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td style=3D"vertical-al=
ign: baseline">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<img
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09src=3D"https://=
cdn.sejutacita.id/assets/email/lock.png"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09width=3D"14px"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09/>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<strong
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>Strengthen the se=
curity of your
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09account</strong
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"color: #7=
67676; margin-top: 8px"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09It=E2=80=99s a met=
hod to help employers know your
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09contact informatio=
n and ensure that
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09important informat=
ion are heading straight
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09to you
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<tr style=3D"margin-top: 8p=
x">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td style=3D"vertical-al=
ign: baseline">
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<img
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09src=3D"https://=
cdn.sejutacita.id/assets/email/suitcase.png"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09width=3D"14px"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09/>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<strong
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>Get exclusive job=
 offers
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09immediately</stron=
g
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09<div
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"color: #7=
67676; margin-top: 8px"
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09Simply finish this=
 verification process &
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09start receiving nu=
merous job invites
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09available
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</tr>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09=09</table>
=09=09=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09<div
=09=09=09=09=09=09=09=09=09=09=09class=3D"container footer"
=09=09=09=09=09=09=09=09=09=09=09style=3D"text-align: center; margin: 0 aut=
o"
=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09<div style=3D"margin: 0px 0px 26px; color:=
 #455869">
=09=09=09=09=09=09=09=09=09=09=09=09This email is generated automatically a=
nd does not need
=09=09=09=09=09=09=09=09=09=09=09=09any reply. If you need any help, contac=
t our
=09=09=09=09=09=09=09=09=09=09=09=09<a
=09=09=09=09=09=09=09=09=09=09=09=09=09href=3D"https://www.instagram.com/de=
alls.jobs/"
=09=09=09=09=09=09=09=09=09=09=09=09=09style=3D"text-decoration: none; colo=
r: #455869"
=09=09=09=09=09=09=09=09=09=09=09=09=09><strong>Support Team</strong></a
=09=09=09=09=09=09=09=09=09=09=09=09>
=09=09=09=09=09=09=09=09=09=09=09=09anytime.
=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09=09<div style=3D"color: #455869">
=09=09=09=09=09=09=09=09=09=09=09=09Copyright &copy; 2026 Dealls Jobs
=09=09=09=09=09=09=09=09=09=09=09=09<br />All Rights Reserved
=09=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09=09</div>
=09=09=09=09=09=09=09=09=09</td>
=09=09=09=09=09=09=09=09</tr>
=09=09=09=09=09=09=09</table>
=09=09=09=09=09=09</div>
=09=09=09=09=09</td>
=09=09=09=09</tr>
=09=09=09</tbody>
=09=09</table>
=09</body>
</html>"""

r = requests.post('http://localhost:8000/parse-and-predict', json={'email_content': raw_email})
result = r.json()

print("=" * 100)
print("PHISHING DETECTION ANALYSIS - WITH EXTRACTED FEATURES")
print("=" * 100)

# Parsed Email
print("\n" + "=" * 100)
print("1. PARSED EMAIL")
print("=" * 100)
print(json.dumps(result["parsed_email"], indent=2))

# Header Features
print("\n" + "=" * 100)
print("2. HEADER FEATURES (13 features)")
print("=" * 100)
if "extracted_features" in result and "header_features" in result["extracted_features"]:
    header_feats = result["extracted_features"]["header_features"]
    if header_feats:
        for key, val in header_feats.items():
            print(f"  {key}: {val}")
    else:
        print("  [No header features extracted]")
else:
    print("  [Header features not available]")

# Text Features
print("\n" + "=" * 100)
print("3. TEXT FEATURES (6 features)")
print("=" * 100)
if "extracted_features" in result and "text_features" in result["extracted_features"]:
    text_feats = result["extracted_features"]["text_features"]
    for key, val in text_feats.items():
        print(f"  {key}: {val}")

# URL Features
print("\n" + "=" * 100)
print("4. URL FEATURES (19 features per URL)")
print("=" * 100)
if "extracted_features" in result and "url_features" in result["extracted_features"]:
    for url_feat in result["extracted_features"]["url_features"]:
        print(f"\n  URL: {url_feat['url']}")
        for key, val in url_feat["features"].items():
            print(f"    {key}: {val}")

# HTML Features
print("\n" + "=" * 100)
print("5. HTML FEATURES (22 features)")
print("=" * 100)
if "extracted_features" in result and "html_features" in result["extracted_features"]:
    html_feats = result["extracted_features"]["html_features"]
    for key, val in html_feats.items():
        print(f"  {key}: {val}")

# Predictions
print("\n" + "=" * 100)
print("6. INDIVIDUAL MODEL PREDICTIONS")
print("=" * 100)
for pred in result["individual_predictions"]:
    print(f"\n  Model: {pred['model']}")
    print(f"    Prediction: {pred['prediction']}")
    print(f"    Confidence: {pred['confidence']:.4f}")
    if 'urls_analyzed' in pred:
        print(f"    URLs Analyzed: {pred['urls_analyzed']}")
        print(f"    Phishing Ratio: {pred['phishing_ratio']:.4f}")

# Combined Analysis
print("\n" + "=" * 100)
print("7. COMBINED ANALYSIS")
print("=" * 100)
combined = result["combined_analysis"]
print(f"  Total Score: {combined['total_score']:.4f}")
print(f"  Final Prediction: {combined['final_prediction']}")
print(f"  Threshold: {combined['threshold']}")
print(f"  Models Used: {combined['models_used']}")
print(f"\n  Weighted Breakdown:")
for breakdown in combined["prediction_breakdown"]:
    print(f"    {breakdown['model']} ({breakdown['weight']*100:.0f}% weight):")
    print(f"      Confidence: {breakdown['confidence']:.4f}")
    print(f"      Weighted Score: {breakdown['weighted_score']:.4f}")

print("\n" + "=" * 100)
