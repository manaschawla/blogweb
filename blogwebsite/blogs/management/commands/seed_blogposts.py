from django.core.management.base import BaseCommand
from blogs.models import Blogpost
from django.utils import timezone
from django.core.files import File
import os
import random

class Command(BaseCommand):
    help = 'Seed the database with 10 unique blog posts with images'

    def handle(self, *args, **kwargs):
        base_path = 'media/blogs/images'
        image_names = [
            'img_develop.jpg',
            'img_travel.jpg',
            'img_food.jpg',
            'img_tech.jpg',
            'img_lifestyle.jpg'
        ]

        titles = [
            "Exploring the Mountains",
            "Street Food Diaries",
            "The Future of AI",
            "Work From Anywhere",
            "Sustainable Living Tips",
            "Mastering Web Development",
            "Hidden Travel Gems",
            "Yoga for Beginners",
            "Gadget Reviews 2025",
            "Cultural Festivals of India"
        ]

        authors = [
            "Aarav Mehta", "Ishita Sharma", "Rohan Verma", "Sneha Kapoor",
            "Vikram Bhat", "Tanya Singh", "Karan Khurana", "Meera Patel",
            "Yash Malhotra", "Priya Saini"
        ]

        headings = [
            ("Adventure Awaits", "Gear Up", "On the Trail"),
            ("Food Fiesta", "Spices and Stories", "A Culinary Ride"),
            ("AI Revolution", "From Sci-fi to Reality", "Future Impact"),
            ("Digital Nomad Life", "Finding Balance", "Tech Essentials"),
            ("Green Living", "Minimalism", "Eco-Habits"),
            ("Code Like a Pro", "Backend vs Frontend", "Build a Portfolio"),
            ("Travel Hacks", "Unexplored Places", "Budget Trips"),
            ("Health is Wealth", "Morning Rituals", "Staying Consistent"),
            ("Tech Talk", "Top Gadgets", "Pros & Cons"),
            ("Indian Culture", "Colorful Celebrations", "Traditions & Tales")
        ]

        contents = [
            ("Trekking through remote trails teaches you life lessons. ",) * 4,
            ("Sampling local food from markets is an unforgettable experience. ",) * 4,
            ("AI is reshaping industries faster than ever imagined. ",) * 4,
            ("Remote work is more than freedom, it’s a responsibility. ",) * 4,
            ("Sustainability begins at home with conscious daily choices. ",) * 4,
            ("Mastering full-stack development opens vast career paths. ",) * 4,
            ("Offbeat destinations are perfect for peace and serenity. ",) * 4,
            ("Yoga improves flexibility, posture, and mental clarity. ",) * 4,
            ("Here are the top gadgets you can’t miss in 2025. ",) * 4,
            ("India’s diversity shines through its regional festivals. ",) * 4,
        ]

        for i in range(10):
            thumb_path = os.path.join(base_path, random.choice(image_names))
            img1_path = os.path.join(base_path, random.choice(image_names))
            img2_path = os.path.join(base_path, random.choice(image_names))

            blog = Blogpost(
                author=authors[i],
                title=titles[i],
                head0=headings[i][0],
                head1=headings[i][1],
                head2=headings[i][2],
                chead0=contents[i][0],
                chead1=contents[i][0],
                chead2=contents[i][0],
                pub_date=timezone.now().date(),
            )

            try:
                with open(thumb_path, 'rb') as f:
                    blog.image_thumbnail.save(os.path.basename(thumb_path), File(f), save=False)
                with open(img1_path, 'rb') as f:
                    blog.image1.save(os.path.basename(img1_path), File(f), save=False)
                with open(img2_path, 'rb') as f:
                    blog.image2.save(os.path.basename(img2_path), File(f), save=False)
            except FileNotFoundError:
                self.stdout.write(self.style.WARNING(f"Missing image file: {thumb_path}, {img1_path}, or {img2_path}"))

            blog.save()

        self.stdout.write(self.style.SUCCESS("Successfully seeded 10 unique blog posts with images!"))
