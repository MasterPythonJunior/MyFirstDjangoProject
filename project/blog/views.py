from django.shortcuts import render, redirect
from django.urls import reverse_lazy

from .models import Category, Article, Comment, Like
from .forms import ArticleForm, LoginForm, RegistrationForm, CommentForm
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth import login, logout
from django.contrib import messages


# Create your views here.


# def index(request):
#     articles = Article.objects.all()
#
#     context = {
#         'title': 'PROWEB-БЛОГ - Главная страница',
#         'articles': articles
#     }
#
#     return render(request, 'blog/index.html', context)


class ArticleListView(ListView):  # article_list.html
    model = Article
    template_name = 'blog/index.html'
    context_object_name = 'articles'  # Иначе имя будет objects
    extra_context = {
        'title': 'Главная страница - PROWEB-БЛОГ'
    }

    def get_queryset(self):
        articles = Article.objects.all()
        sort_field = self.request.GET.get('sort')
        if sort_field:
            articles = articles.order_by(sort_field)
        return articles



# def articles_by_category(request, category_id):
#     articles = Article.objects.filter(category_id=category_id)
#     category = Category.objects.get(pk=category_id)
#     context = {
#         'title': f'Категория: {category.title}',
#         'articles': articles
#     }
#
#     return render(request, 'blog/index.html', context)

class ArticleByCategory(ArticleListView):
    # переделать стандартный вывод статей (ВСЕХ)
    def get_queryset(self):
        articles = Article.objects.filter(category_id=self.kwargs['category_id'])
        sort_field = self.request.GET.get('sort')
        if sort_field:
            articles = articles.order_by(sort_field)
        return articles

    # Динамическая отправка контекста
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data()  # Все что было и так сохранить
        category = Category.objects.get(pk=self.kwargs['category_id'])
        context['title'] = f'Категория: {category.title}'
        return context


# def article_detail(request, article_id):
#     article = Article.objects.get(pk=article_id)
#     context = {
#         'article': article,
#         'title': f'Статья: {article.title}'
#     }
#     return render(request, 'blog/article_detail.html', context)
#

class ArticleDetailView(DetailView):  # article_detail.html
    model = Article
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        article = Article.objects.get(pk=self.kwargs['pk'])
        article.views += 1
        article.save()
        user = self.request.user
        if user.is_authenticated:
            mark, created = Like.objects.get_or_create(user=user, article=article)
            print(mark)
            if created:
                context['like'] = False
                context['dislike'] = False
            else:
                context['like'] = mark.like
                context['dislike'] = mark.dislike
        else:
            context['like'] = False
            context['dislike'] = False
        context['title'] = f'Статья на тему: {article.title}'
        if self.request.user.is_authenticated:
            context['comment_form'] = CommentForm()
        context['comments'] = Comment.objects.filter(article_id=self.kwargs['pk'])
        return context


# def add_article(request):
#     if request.method == 'POST':
#         form = ArticleForm(request.POST, request.FILES)
#         if form.is_valid():
#             # form.cleaned_data
#             # title = form.cleaned_data['title']
#             article = Article.objects.create(**form.cleaned_data)
#             article.save()
#             return redirect('article_detail', article.pk)
#     else:
#         form = ArticleForm()
#
#     context = {
#         'form': form,
#         'title': 'Добавить статью'
#     }
#     return render(request, 'blog/article_form.html', context)
#

class NewArticle(CreateView):  # GET POST не надо делать Класс сделает все сам
    form_class = ArticleForm
    template_name = 'blog/article_form.html'
    extra_context = {
        'title': 'Добавить статью'
    }


class ArticleUpdate(UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = 'blog/article_form.html'


class ArticleDelete(DeleteView):
    model = Article
    success_url = reverse_lazy('index')  # куда перейти после удаления
    context_object_name = 'article'


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user:
                login(request, user)
                messages.success(request, 'Вы успешно вошли в аккаунт!')
                return redirect('index')
            else:
                messages.error(request, 'Не верные логин/пароль')
                return redirect('login')
        else:
            return redirect('login')
    else:
        form = LoginForm()

    context = {
        'title': 'Авторизация пользователя',
        'form': form
    }
    return render(request, 'blog/user_login.html', context)


def user_logout(request):
    logout(request)
    messages.warning(request, 'Вы вышли из аккаунта')
    return redirect('index')


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            # login(request, user)
            messages.success(request, 'Регистрация прошла успешно. Войдите в аккаунт.')
            return redirect('login')
        else:
            for field in form.errors:
                messages.error(request, form.errors[field].as_text())
            return redirect('register')
    else:
        form = RegistrationForm()
    context = {
        'form': form,
        'title': 'Регистрация пользователя'
    }
    return render(request, 'blog/register.html', context)


def save_comment(request, pk):
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.article = Article.objects.get(pk=pk)
        comment.user = request.user
        comment.save()
        messages.success(request, 'Ваш комментарий успешно сохранен')
        return redirect('article_detail', pk)


"""Оформить красиво комментарии
Вывод ошибок при регистрации
Лайки и Дизлайки
Отображение в админке комментариев"""


def add_or_delete_mark(request, article_id, action):
    user = request.user
    if user.is_authenticated:
        article = Article.objects.get(pk=article_id)
        mark, created = Like.objects.get_or_create(user=user, article=article)
        if action == 'addlike':
            mark.like = True
            mark.dislike = False
        elif action == 'adddislike':
            mark.like = False
            mark.dislike = True
        elif action == 'deletelike':
            mark.like = False
        elif action == 'deletedislike':
            mark.dislike = False
        mark.save()
        return redirect('article_detail', article.pk)
    else:
        return redirect('login')

"""
Поисковик
Фильтр статей на главной
Уникальные просмотры - видео
Страница аккаунта 
Слайдер последних статей - видос
Удаление своих комментариев - видео
"""

class SearchResults(ArticleListView):
    def get_queryset(self):
        word = self.request.GET.get('q')
        articles = Article.objects.filter(title__icontains=word)
        return articles



def profile(request):
    return render(request, 'blog/profile.html')




