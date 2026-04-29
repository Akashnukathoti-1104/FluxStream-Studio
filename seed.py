from datetime import date, timedelta

from app import create_app
from app.extensions import db
from app.models import Analytics, User, Video

SEED_VIDEOS = [
    ("Deep Space: Journey Beyond Our Galaxy - Ep.4", "Science", 2400000, 2901, True),
    ("Amazon Rainforest: Night Creatures Documentary", "Nature", 891000, 3840, False),
    ("Quantum Computing Explained - Beginner to Pro", "Tech", 1100000, 1325, False),
    ("Formula E 2025 Season Highlights Megacut", "Sports", 3200000, 4364, False),
    ("Ocean Abyss: Creatures of 6,000m Depth", "Nature", 744000, 1877, False),
    ("AI vs Human: The Future of Creativity 2025", "Tech", 2000000, 3330, False),
]


def run_seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        user = User.query.filter_by(username='arjun_kumar').first()
        if not user:
            user = User(
                username='arjun_kumar',
                email='arjun@nexstream.local',
                password_hash='seeded-demo-user',
                role='creator',
                plan='pro',
                subscriber_count=128000,
            )
            db.session.add(user)
            db.session.flush()

        if Video.query.count() == 0:
            for index, row in enumerate(SEED_VIDEOS, start=1):
                title, category, views, duration, is_live = row
                video = Video(
                    user_id=user.id,
                    title=title,
                    description=f'{title} generated sample listing for NexStream 2.0.',
                    tags='demo,seed,ai,streaming',
                    category=category,
                    status='live',
                    hls_playlist_url=f'/stream/{index}/playlist.m3u8',
                    thumbnail_url=f'https://picsum.photos/seed/nexstream-{index}/1280/720',
                    duration_seconds=duration,
                    resolution='3840x2160' if duration > 3000 else '1920x1080',
                    file_size_bytes=duration * 150000,
                    view_count=views,
                    like_count=max(views // 30, 100),
                    is_live=is_live,
                )
                db.session.add(video)

            db.session.flush()
            videos = Video.query.all()
            for offset in range(30):
                day = date.today() - timedelta(days=offset)
                for video in videos:
                    views = max(video.view_count // (offset + 10), 50)
                    clicks = max(views // 5, 10)
                    analytics = Analytics(
                        video_id=video.id,
                        date=day,
                        views=views,
                        watch_minutes=max((video.duration_seconds or 60) * views // 60, 1),
                        clicks=clicks,
                        ctr=clicks / views,
                        revenue_usd=round((views / 1000.0) * 2.5, 2),
                    )
                    db.session.add(analytics)

        db.session.commit()
        print('Seed complete.')


if __name__ == '__main__':
    run_seed()
