-- Active: 1778311386133@@127.0.0.1@3306

select u.username, u.email, p.title, p.content, p.created_at from users as u join posts as p on u.id = p.user_id;

SELECT * FROM posts;
