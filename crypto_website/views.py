import os
import qrcode

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from contacts.models import Contact
from crypto.models import PriceData, Cryptocurrency
from posts.models import Post, PostCategory, Comment


def home(request):
    max_posts_per_category = settings.MAX_POSTS_PER_CATEGORY_LIMIT

    categories = PostCategory.objects.filter(is_active=True).order_by("name")

    categories_to_keep = []
    for category in categories:
        posts = Post.objects.filter(category=category, is_published=True).order_by(
            "-published_at"
        )[:max_posts_per_category]

        if posts.exists():
            category.posts = posts
            categories_to_keep.append(category)

        categories = categories_to_keep

    context = {"categories": categories}

    return render(request, "home.html", context)


def whitepaper(request):
    context = {}
    return render(request, "whitepaper.html", context)


def about(request):
    context = {}
    return render(request, "about.html", context)


def contact(request):
    context = {"messages": messages.get_messages(request)}
    return render(request, "contact.html", context)


def faq(request):
    context = {}
    return render(request, "faq.html", context)


def live(request):
    prices = []
    cryptocurrencies = Cryptocurrency.objects.all()
    for cryptocurrency in cryptocurrencies:
        price_data = PriceData.objects.filter(cryptocurrency=cryptocurrency).order_by(
            "-timestamp"
        )[:30]

        new_price_data = {
            "id": cryptocurrency.id,
            "name": cryptocurrency.name,
            "display_name": cryptocurrency.display_name,
            "symbol": cryptocurrency.symbol,
            "icon": cryptocurrency.icon,
            "slug": cryptocurrency.slug,
            "labels": [
                data.timestamp.strftime("%d %B, %H:%M:%S") for data in price_data
            ],
            "prices": [str(data.price_usd) for data in price_data],
        }

        if len(new_price_data["prices"]) < 1:
            continue

        prices.append(new_price_data)

    context = {
        "prices": prices,
    }

    return render(request, "live.html", context)


def donate(request):
    bitcoin_address = settings.DONATE_BITCOIN_ADDRESS
    ethereum_address = settings.DONATE_ETHEREUM_ADDRESS

    bitcoin_qrcode_file_name = "donate_bitcoin_qrcode.png"
    ethereum_qrcode_file_name = "donate_ethereum_qrcode.png"

    # Create qr directory if it doesn't exist
    qr_dir = os.path.join(settings.MEDIA_ROOT, "qr")
    os.makedirs(qr_dir, exist_ok=True)

    # Generate QR codes
    bitcoin_qr_path = os.path.join(qr_dir, bitcoin_qrcode_file_name)
    ethereum_qr_path = os.path.join(qr_dir, ethereum_qrcode_file_name)

    bitcoin_qr = qrcode.make(bitcoin_address)
    ethereum_qr = qrcode.make(ethereum_address)

    bitcoin_qr.save(bitcoin_qr_path)
    ethereum_qr.save(ethereum_qr_path)

    context = {
        "bitcoin": bitcoin_address,
        "ethereum": ethereum_address,
        "bitcoin_qr": os.path.join(settings.MEDIA_URL, "qr", bitcoin_qrcode_file_name),
        "ethereum_qr": os.path.join(settings.MEDIA_URL, "qr", ethereum_qrcode_file_name),
    }
    return render(request, "donate.html", context)


def rss_feed(request):
    rss_item_count = settings.RSS_FEED_LIMIT
    posts = Post.objects.filter(is_published=True).order_by("-published_at")[
        :rss_item_count
    ]
    context = {
        "posts": posts,
    }
    return render(request, "rss_feed.xml", context, content_type="application/xml")


def post_detail(request, slug):
    max_item_sidebar_widget_limit = settings.MAX_ITEM_SIDEBAR_WIDGET_LIMIT

    try:
        post = Post.objects.get(slug=slug, is_published=True)
    except Post.DoesNotExist:
        return render(request, "404.html", status=404)

    # Increment view count
    post.views_count += 1
    post.save()

    # Get latest posts for sidebar widget
    latest_posts = (
        Post.objects.filter(is_published=True)
        .exclude(id=post.id)
        .order_by("-published_at")[:max_item_sidebar_widget_limit]
    )

    # Get latest news for sidebar widget
    from news.models import NewsArticle

    latest_news = NewsArticle.objects.filter(is_published=True).order_by(
        "-published_at"
    )[:max_item_sidebar_widget_limit]

    prices = {}
    for crypto in post.related_cryptocurrencies.all():
        price_data = PriceData.objects.filter(cryptocurrency=crypto).order_by(
            "-timestamp"
        )[:30]
        prices[crypto.id] = {
            "labels": [
                data.timestamp.strftime("%d %B, %H:%M:%S") for data in price_data
            ],
            "prices": [str(data.price_usd) for data in price_data],
        }

    comments = Comment.objects.filter(post=post).order_by("created_at")

    context = {
        "post": post,
        "latest_posts": latest_posts,
        "latest_news": latest_news,
        "prices": prices,
        "comments": comments,
    }

    return render(request, "post_detail.html", context)


def crypto_posts(request, slug):
    max_item_sidebar_widget_limit = settings.MAX_ITEM_SIDEBAR_WIDGET_LIMIT
    posts_per_page = settings.POSTS_PER_PAGE_LIMIT

    try:
        cryptocurrency = Cryptocurrency.objects.get(slug=slug)
    except Cryptocurrency.DoesNotExist:
        return render(request, "404.html", status=404)

    # Get posts for this cryptocurrency
    posts = Post.objects.filter(
        related_cryptocurrencies=cryptocurrency, is_published=True
    ).order_by("-published_at")

    # Pagination
    paginator = Paginator(posts, posts_per_page)
    page = request.GET.get("page")
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        return render(request, "404.html", status=404)

    # Get latest news for sidebar widget
    from news.models import NewsArticle

    latest_news = NewsArticle.objects.filter(is_published=True).order_by(
        "-published_at"
    )[:max_item_sidebar_widget_limit]

    latest_posts = Post.objects.filter(is_published=True).order_by("-published_at")[
        :max_item_sidebar_widget_limit
    ]

    context = {
        "cryptocurrency": cryptocurrency,
        "posts": posts,
        "latest_news": latest_news,
        "latest_posts": latest_posts,
        "is_paginated": paginator.num_pages > 1,
        "page_obj": posts,
    }

    return render(request, "crypto_posts.html", context)


def category_posts(request, slug):
    max_item_sidebar_widget_limit = settings.MAX_ITEM_SIDEBAR_WIDGET_LIMIT
    posts_per_page = settings.POSTS_PER_PAGE_LIMIT

    try:
        category = PostCategory.objects.get(slug=slug, is_active=True)
    except PostCategory.DoesNotExist:
        return render(request, "404.html", status=404)

    # Get posts for this category
    posts = Post.objects.filter(category=category, is_published=True).order_by(
        "-published_at"
    )

    # Pagination
    paginator = Paginator(posts, posts_per_page)
    page = request.GET.get("page")
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        return render(request, "404.html", status=404)

    # Get latest news for sidebar widget
    from news.models import NewsArticle

    latest_news = NewsArticle.objects.filter(is_published=True).order_by(
        "-published_at"
    )[:max_item_sidebar_widget_limit]

    latest_posts = Post.objects.filter(is_published=True).order_by("-published_at")[
        :max_item_sidebar_widget_limit
    ]

    context = {
        "category": category,
        "posts": posts,
        "latest_news": latest_news,
        "latest_posts": latest_posts,
        "is_paginated": paginator.num_pages > 1,
        "page_obj": posts,
    }

    return render(request, "category_posts.html", context)


def like_post(request, slug):
    try:
        post = Post.objects.get(slug=slug, is_published=True)
    except Post.DoesNotExist:
        return render(request, "404.html", status=404)

    # Get client IP
    client_ip = request.META.get(
        "HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR")
    )

    from posts.models import PostInteractionLog

    # Check for existing dislike and remove it
    dislike_interaction = PostInteractionLog.objects.filter(
        post=post, ip_address=client_ip, interaction_type="dislike"
    ).first()

    if dislike_interaction:
        dislike_interaction.delete()
        post.dislikes_count = max(0, post.dislikes_count - 1)
        post.save()

    # Check for existing like
    like_interaction = PostInteractionLog.objects.filter(
        post=post, ip_address=client_ip, interaction_type="like"
    ).exists()

    if not like_interaction:
        post.likes_count += 1
        post.save()

        # Log the interaction
        PostInteractionLog.objects.create(
            post=post, ip_address=client_ip, interaction_type="like"
        )

    return redirect("post_detail", slug=post.slug)


def dislike_post(request, slug):
    try:
        post = Post.objects.get(slug=slug, is_published=True)
    except Post.DoesNotExist:
        return render(request, "404.html", status=404)

    # Get client IP
    client_ip = request.META.get(
        "HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR")
    )

    from posts.models import PostInteractionLog

    # Check for existing like and remove it
    like_interaction = PostInteractionLog.objects.filter(
        post=post, ip_address=client_ip, interaction_type="like"
    ).first()

    if like_interaction:
        like_interaction.delete()
        post.likes_count = max(0, post.likes_count - 1)
        post.save()

    # Check for existing dislike
    dislike_interaction = PostInteractionLog.objects.filter(
        post=post, ip_address=client_ip, interaction_type="dislike"
    ).exists()

    if not dislike_interaction:
        post.dislikes_count += 1
        post.save()

        # Log the interaction
        PostInteractionLog.objects.create(
            post=post, ip_address=client_ip, interaction_type="dislike"
        )

    return redirect("post_detail", slug=post.slug)


def short_url(request):
    post_id = request.GET.get("p")
    if not post_id:
        return render(request, "404.html", status=404)

    try:
        post = Post.objects.get(id=post_id, is_published=True)
        return redirect("post_detail", slug=post.slug)
    except Post.DoesNotExist:
        return render(request, "404.html", status=404)
    post.save()

    return redirect("post_detail", slug=post.slug)


def submit_contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        if not all([name, email, subject, message]):
            messages.error(request, "Please fill in all required fields.")
            return redirect("contact")

        # Create and save the contact message
        Contact.objects.create(name=name, email=email, subject=subject, message=message)

        messages.success(request, "Your message has been sent successfully!")
        return redirect("contact")

    messages.error(request, "Invalid request method.")
    return redirect("contact")


def submit_comment(request, slug):
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("home")

    parent_id = request.POST.get("parent_id")
    name = request.POST.get("name")
    email = request.POST.get("email")
    content = request.POST.get("content")

    # Validate required fields
    if not all([slug, name, email, content]):
        messages.error(request, "Please fill in all required fields.")
        return redirect("post_detail", slug=slug)

    try:
        post = Post.objects.get(slug=slug, is_published=True)
    except Post.DoesNotExist:
        messages.error(request, "Post not found.")
        return redirect("home")

    # Handle parent comment if this is a reply
    parent = None
    if parent_id:
        try:
            parent = Comment.objects.get(id=parent_id, post=post)
        except Comment.DoesNotExist:
            messages.error(request, "Parent comment not found.")
            return redirect("post_detail", slug=slug)

    # Create the comment
    Comment.objects.create(
        post=post,
        parent=parent,
        name=name,
        email=email,
        content=content,
        is_approved=False,
    )

    messages.success(
        request, "Your comment has been submitted and is awaiting moderation."
    )
    return redirect("post_detail", slug=slug)
