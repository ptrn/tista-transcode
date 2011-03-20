TRUNCATE TABLE movie;
TRUNCATE TABLE movie_format;
TRUNCATE TABLE user;
TRUNCATE TABLE poster;

INSERT INTO user (id, username, email) VALUES (1,'larspbjo','l@l6.no');
INSERT INTO poster (id,path) VALUES (1,'ted-richard-poster.png');
INSERT INTO poster (id,path) VALUES (2,'ted-derek-poster.png');
INSERT INTO movie (id, title, description, duration, author, poster_id) VALUES (1, 'TED-talk', 'this is the first video that has been added', '210310', 1, 1);
INSERT INTO movie_format (movie_id, format, path) VALUES (1, 'ogg', 'ted-richard.ogv');
INSERT INTO movie_format (movie_id, format, path) VALUES (1, 'mp4', 'ted-richard.mp4');
INSERT INTO movie (id, title, description, duration, author, poster_id) VALUES (2, '2nd TED-talk', 'second added video, this time also from TED', '225760', 1, 2);
INSERT INTO movie_format (movie_id, format, path) VALUES (2, 'ogg', 'ted-derek.ogv');
INSERT INTO movie_format (movie_id, format, path) VALUES (2, 'mp4', 'ted-derek.mp4');
