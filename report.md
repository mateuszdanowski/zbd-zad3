###### Mateusz Danowski

# Zadanie świąteczne
W zadaniu poproszeni jesteśmy o pomoc elfom w zoptymalizowaniu systemu pakowania paczek. W tym celu, aby móc wybrać odpowiednie rozwiązanie, przeprowadziłem eksperymenty na różnych algorytmach i wielkościach danych. Przyjąłem, że różnych słodyczy zawsze będzie 5, każdy z nich będzie podobny do każdego innego (z różnym podobieństwem), oraz każdy list będzie zawierał od 1 do 5 pozycji. Programy przeze mnie napisane znajdują się w repozytorium pod tym [linkiem](https://github.com/mateuszdanowski/zbd-zad3).

#### Jak bardzo słaby jest obecny system pakowania paczek?
Przetestujmy obecny algorytm dla najprostszego przypadku. Niech liczba każdego ze słodyczy będzie nieograniczona i niech każdy elf ma tylko 5 paczek do skompletowania. Wyniki zamieściłem w poniższej tabeli.

numer elfa | % udanych transakcji | czas działania (s)
-|-|-
1|20|75.28
2|0|64.98
3|0|69.19
4|0|73.28
5|20|64.96
6|0|49.64
7|40|64.99
8|20|63.99
9|60|76.28
10|20|71.19
11|20|45.55
12|20|76.27
13|20|68.2
14|40|63.97
15|20|70.18
16|40|76.26
17|0|54.68
18|20|75.25
19|20|51.71
20|20|69.19

Rzeczywiście obecny system pakowania paczek jest lekko mówiąc słaby. Średnia liczba udanych transakcji wynosi 20%, a średni czas pracy elfa to około 66 sekund. W trakcie symulacji pojawia się masa błędów, które informormują nas o niepowodzeniu komendy `UPDATE`. Nie wykonuje się ona poprawnie, ponieważ postgres w tym samym czasie wykrywa zakleszczenie.

#### Pomysły na usprawnienie systemu

Zastanówmy się dlaczego w trakcie kompletowania przesyłek pojawiają się błędy. Elfy domyślnie wykonują transakcje w trybie `READ COMMITTED`. Oznacza to, że pomiędzy sprawdzeniem liczby danego cukierka, pobraniem potrzebnej liczby cukierków oraz uaktualnieniem liczby cukierków w magazynie, inna transakcja może zmienić liczbę tego samego cukierka, co może spowodować złamanie zasady z tabeli `candies_in_stock`: `CHECK(in_stock >= 0)`. Zastanówmy się, czy istnieje bardziej optymalny sposób przetwarzania cukierków z listy. Nie jesteśmy zmuszeni do przetwarzania ich po kolei, zatem spróbujmy posortować każdy taki list dla każdego elfa i zobaczmy czy nastąpi jakaś zmiana.

numer elfa | % udanych transakcji | czas działania (s)
-|-|-
1|100|0.19
2|100|0.06
3|100|0.07
4|100|0.04
5|100|0.06
6|100|0.1
7|100|0.04
8|100|0.12
9|100|0.03
10|100|0.06
11|100|0.14
12|100|0.12
13|100|0.14
14|100|0.14
15|100|0.04
16|100|0.12
17|100|0.16
18|100|0.13
19|100|0.15
20|100|0.12

Wygląda na to, że posortowanie cukierków na liście dla każdego elfa jest świetnym pomysłem. Na najprostszym przykładzie elfy poradziły sobie ze wszystkimi listami, uzyskując znakomity czas, wynoszący średnio 0.1 sekundy. Jest to dobry krok w optymalizacji systemu pakowania paczek.

#### Praca na trudniejszych danych

Po powyższym sukcesie, powinniśmy sprawdzić jak zmiana kolejności przetwarzania cukierków radzi sobie na większych, bardziej skomplikowanych danych. Dla 20-krotnego zwiększenia liczby listów dla każdego elfa, średni czas pracy wzrósł prawie 30-krotnie (2.83s). Jest to wzrost liniowy, więc możemy uznać to za sukces. Skoro zwiększenie liczby listów nie powoduje błędów w naszym rozwiązaniu, zobaczmy co się dzieje dla niewystarczającej liczby pewnych cukierków. Niech liczba cukierków w magazynie wynosi kolejno 1, 10, 10, 10, 10000, a liczba listów do przetworzenia dla każdego elfa to 10.

numer elfa | % udanych transakcji | czas działania (s)
-|-|-
1|80|14.69
2|40|14.6
3|100|14.75
4|90|14.61
5|80|14.66
6|50|14.46
7|70|14.72
8|80|14.74
9|70|14.59
10|80|14.58
11|100|14.69
12|90|14.64
13|60|14.69
14|80|14.72
15|90|14.59
16|70|14.71
17|90|14.78
18|90|14.69
19|100|14.74
20|80|14.7

Wyraźnie widać, że zaczynają pojawiać się pewne problemy. Już nie wszystkie transakcje się udają (średnia skuteczność wynosi 79.5%) oraz średni czas pracy elfa znacząco wzrósł (14.67 s). W trakcie kompletowania przesyłek ponownie zaczynają pojawiać się informacje o błędach. Tak jak poprzednio, są to błędy spowodowane wykryciem zakleszczenia, ale także błędy dotyczące złamania zasady z tabeli `candies_in_stock`. Zobaczmy jak zachowa się algorytm, gdy transakcje będą się wykonywać w trybie `SERIALIZABLE`. Samo dodanie linijki `conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_SERIALIZABLE)` nie wystarcza, ponieważ niektóre elfy zupełnie przerywają swoją pracę przez błąd wychodzący z biblioteki `psycopg2`, informujący o niemożliwości zserializowania dostępu do bazy danych. Dostajemy także wskazówkę, by spróbować ponowić transakcję w przypadku jej niepowodzenia. Pomyśleć musimy o ustaleniu limitu prób. Dopiero od 1000, średnia liczba zrealizowanych transakcji utrzymuje się powyżej 60%. Dla 10000 wyniki prezentują się następująco:

numer elfa | % udanych transakcji | czas działania (s)
-|-|-
1|80|7.94
2|70|9.31
3|90|4.97
4|90|5.27
5|80|7.93
6|100|0.21
7|90|5.43
8|80|8.13
9|90|5.35
10|90|5.07
11|90|5.5
12|100|0.04
13|70|9.36
14|90|4.77
15|100|0.05
16|80|7.94
17|80|8.11
18|60|9.85
19|90|4.87
20|80|8.11

Od razu rzuca się w oczy czas działania elfów, ktory jest znacząco krótszy i średnio równy 5.91s. Jest to spadek prawie 2.5-krotny w porównaniu z poprzednim algorytmem. Wzrosła także średnia liczba udanych transakcji (85%). To rozwiązanie wydaje się być zadowalające.

#### Inne ciekawe pomysły
Elfy przetwarzają list cukierek po cukierku, wykonując co krok `UPDATE` w tabeli `candies_in_stock`. Zauważmy, że wcale nie muszą tego robić za każdym razem gdy przetworzą dany cukierek z listu, lecz mogą spróbować wykonać serię takich updatów na koniec.

numer elfa | % udanych transakcji | czas działania (s)
-|-|-
1|90|5.64
2|90|5.45
3|90|5.68
4|90|5.42
5|80|8.97
6|80|8.8
7|60|10.53
8|80|8.76
9|90|5.57
10|90|6.01
11|80|8.63
12|90|5.76
13|100|0.07
14|90|5.88
15|80|8.95
16|70|9.87
17|90|6.09
18|70|9.93
19|80|8.85
20|80|8.76

Średni procent udanych transakcji wyniósł 83.5%, a średni czas działania elfa to 7.18s. Wygląda na to, że nie jest to znacząca zmiana w algorytmie. Produkuje ona nieco gorsze wyniki w porównaniu do poprzedniego rozwiązania. Ciekawa jest zależność między czasem działania elfa, a liczbą zrealizowanych transakcji. Elfy, które szybciej skończą, mają więcej udanych transakcji od tych elfów, którym praca zajęła dłużej.

#### Przykład złośliwego adwersarza

W zadaniu proszeni jesteśmy o wymyślenie przykładu złośliwego elfa. Do odegrania tej roli wybrałem elfa numer 10, który to szedł spać na 0.5 sekundy w różnych miejscach w trakcie realizowania transakcji. Algorytm, który uzyskałem na końcu nie miał z takim zachowaniem większych kłopotów.

numer elfa | % udanych transakcji | czas działania (s)
-|-|-
1|80|11.82
2|80|12.23
3|70|14.13
4|80|12.08
5|80|12.47
6|90|6.82
7|80|12.18
8|100|0.51
9|80|12.29
10|70|72.31
11|90|7.17
12|50|15.49
13|90|7.62
14|90|8.35
15|90|8.19
16|70|13.66
17|90|7.88
18|80|12.35
19|60|14.78
20|90|7.13

Średnia liczba udanych transakcji utrzymała się na wysokim poziomie 80.5%, a średni czas pracy elfów został zawyżony przez adwersarza i wyniósł 11.5s.

#### Podsumowanie
Ostatecznie udało mi się usprawnić algorytm w trzech krokach. Pierwszy z nich to posortowanie listy cukierków dla każdego listu. Dzięki temu algorytm zaczął poprawnie rozwiązywać problemy zakleszczeń, skutkiem czego liczba udanych transakcji wzrosła oraz średni czas pracy elfa spadł. Kolejnym krokiem było ustawienie poziomu izolacji transakcji na `SERIALIZABLE`, które doprowadziło do ostatniego kroku optymalizacji, czyli powtarzania transakcji w razie ich niepowodzenia. Dzięki tym rozwiązaniom, procent udanych transakcji regularnie wynosił ponad 80%, a średni czas działania elfów rósł liniowo względem liczby listów.



