from __future__ import annotations

from datetime import date, datetime, timedelta

from app.extensions import db
from app.models import Analytics, User, Video


SAMPLE_VIDEOS = [
    {
        'title': 'Deep Space: Journey Beyond Our Galaxy - Ep.4',
        'description': 'An epic cinematic journey through the cosmos, exploring nebulae, black holes, and the edges of our observable universe.',
        'category': 'Science',
        'tags': 'space,cosmos,documentary,4k,nasa',
        'duration_seconds': 2901,
        'view_count': 2400000,
        'like_count': 184000,
        'status': 'live',
        'is_live': True,
        'thumbnail_url': 'https://picsum.photos/seed/space1/1280/720',
        'embed_url': 'https://www.youtube.com/embed/HSzCXDQHc10',
        'resolution': '4K',
        'file_size_bytes': 4200000000,
    },
    {
        'title': 'Amazon Rainforest: Night Creatures Documentary',
        'description': 'Deep inside the Amazon, a world wakes up at night. Rare footage of nocturnal creatures in their natural habitat.',
        'category': 'Nature',
        'tags': 'nature,amazon,wildlife,documentary,night',
        'duration_seconds': 3840,
        'view_count': 891000,
        'like_count': 62000,
        'status': 'live',
        'is_live': False,
        'thumbnail_url': 'https://picsum.photos/seed/jungle2/1280/720',
        'embed_url': 'https://www.youtube.com/embed/LXb3EKWsInQ',
        'resolution': '1080p',
        'file_size_bytes': 1800000000,
    },
    {
        'title': 'Quantum Computing Explained - Beginner to Pro',
        'description': 'From qubits to quantum supremacy — a complete visual explainer on how quantum computers work and why they matter.',
        'category': 'Tech',
        'tags': 'quantum,computing,technology,education,ai',
        'duration_seconds': 1325,
        'view_count': 1100000,
        'like_count': 97000,
        'status': 'live',
        'is_live': False,
        'thumbnail_url': 'https://picsum.photos/seed/tech3/1280/720',
        'embed_url': 'https://www.youtube.com/embed/JhHMJCUmq28',
        'resolution': '1080p',
        'file_size_bytes': 620000000,
    },
    {
        'title': 'Formula E 2025 Season Highlights Megacut',
        'description': 'Every breathtaking overtake, crash, and championship moment from the 2025 Formula E season in one epic megacut.',
        'category': 'Sports',
        'tags': 'formulae,racing,motorsport,electric,highlights',
        'duration_seconds': 4364,
        'view_count': 3200000,
        'like_count': 241000,
        'status': 'live',
        'is_live': False,
        'thumbnail_url': 'https://picsum.photos/seed/racing4/1280/720',
        'embed_url': 'https://www.youtube.com/embed/ysz5S6PUM-U',
        'resolution': '4K',
        'file_size_bytes': 3100000000,
    },
    {
        'title': 'Ocean Abyss: Creatures of 6,000m Depth',
        'description': 'Never-before-seen footage from 6 kilometers beneath the Pacific Ocean — bioluminescent, alien-like creatures in total darkness.',
        'category': 'Nature',
        'tags': 'ocean,deepSea,creatures,nature,documentary,8k',
        'duration_seconds': 1877,
        'view_count': 744000,
        'like_count': 58000,
        'status': 'live',
        'is_live': False,
        'thumbnail_url': 'https://picsum.photos/seed/ocean5/1280/720',
        'embed_url': 'https://www.youtube.com/embed/4UVh7bHb6oE',
        'resolution': '1080p',
        'file_size_bytes': 980000000,
    },
    {
        'title': 'AI vs Human: The Future of Creativity 2025',
        'description': 'Can machines truly be creative? A deep documentary exploring how AI is reshaping art, music, writing, and human identity.',
        'category': 'Tech',
        'tags': 'ai,creativity,future,art,technology,documentary',
        'duration_seconds': 3330,
        'view_count': 2000000,
        'like_count': 156000,
        'status': 'live',
        'is_live': False,
        'thumbnail_url': 'https://picsum.photos/seed/ai6/1280/720',
        'embed_url': 'https://www.youtube.com/embed/56mGTszb_iM',
        'resolution': '1080p',
        'file_size_bytes': 1560000000,
    },
]


def seed(app=None):
    if app is None:
        from app import create_app

        app = create_app()

    with app.app_context():
        db.create_all()

        user = User.query.filter_by(username='arjun_kumar').first()
        if not user:
            user = User(
                username='arjun_kumar',
                email='arjun@nexstream.io',
                role='creator',
                plan='pro',
                subscriber_count=128000,
            )
            user.set_password('nexstream123')
            db.session.add(user)
            db.session.flush()

        if Video.query.count() == 0:
            for index, data in enumerate(SAMPLE_VIDEOS, start=1):
                video = Video(
                    user_id=user.id,
                    title=data['title'],
                    description=data['description'],
                    category=data['category'],
                    tags=data['tags'],
                    embed_url=data['embed_url'],
                    status=data['status'],
                    is_live=data['is_live'],
                    thumbnail_url=data['thumbnail_url'],
                    hls_playlist_url=data['embed_url'],
                    duration_seconds=data['duration_seconds'],
                    resolution=data['resolution'],
                    file_size_bytes=data['file_size_bytes'],
                    view_count=data['view_count'],
                    like_count=data['like_count'],
                    created_at=datetime.utcnow() - timedelta(days=index * 2),
                )
                db.session.add(video)
                db.session.flush()

                for day in range(14):
                    day_views = max(int(data['view_count'] / 45 * (1.15 - (day * 0.03))), 20)
                    db.session.add(
                        Analytics(
                            video_id=video.id,
                            date=date.today() - timedelta(days=13 - day),
                            views=day_views,
                            watch_minutes=max(int(day_views * (video.duration_seconds or 0) / 60 * 0.35), 1),
                            clicks=max(int(day_views * 0.08), 1),
                            ctr=round(6.5 + (day % 5) * 0.4, 2),
                            revenue_usd=round(day_views / 1000.0 * 2.5, 2),
                        )
                    )

        db.session.commit()
        print('Seed complete.')


def run_seed():
    seed()


if __name__ == '__main__':
    run_seed()