// Quiz Rápido — server-side game logic

const QUESTIONS = [
  // PORTUGAL & CULTURA
  { q: 'Qual é a capital de Portugal?', options: ['Porto', 'Lisboa', 'Braga', 'Faro'], answer: 1 },
  { q: 'Quem escreveu "Os Lusíadas"?', options: ['Fernando Pessoa', 'Eça de Queirós', 'Luís de Camões', 'Gil Vicente'], answer: 2 },
  { q: 'Em que ano Portugal ganhou o Euro de futebol?', options: ['2012', '2016', '2020', '2004'], answer: 1 },
  { q: 'Qual é o rio mais longo de Portugal?', options: ['Douro', 'Tejo', 'Guadiana', 'Minho'], answer: 1 },
  { q: 'Quantos distritos tem Portugal Continental?', options: ['16', '18', '20', '22'], answer: 1 },
  { q: 'Quem foi o primeiro rei de Portugal?', options: ['D. Afonso II', 'D. Dinis', 'D. Afonso Henriques', 'D. Sancho I'], answer: 2 },
  { q: 'Em que ano foi a Revolução dos Cravos?', options: ['1968', '1972', '1974', '1976'], answer: 2 },
  { q: 'Qual é a maior ilha dos Açores?', options: ['Faial', 'Terceira', 'São Miguel', 'Pico'], answer: 2 },
  { q: 'Qual prato é tipicamente português?', options: ['Paella', 'Bacalhau à Brás', 'Gazpacho', 'Tortilla'], answer: 1 },
  { q: 'Em que século chegaram os portugueses à Índia?', options: ['XIV', 'XV', 'XVI', 'XVII'], answer: 1 },
  { q: 'Quem descobriu o caminho marítimo para a Índia?', options: ['Pedro Álvares Cabral', 'Bartolomeu Dias', 'Vasco da Gama', 'Fernão de Magalhães'], answer: 2 },
  { q: 'Qual é o estilo arquitetónico do Mosteiro dos Jerónimos?', options: ['Barroco', 'Gótico', 'Manuelino', 'Renascentista'], answer: 2 },
  { q: 'A que cidade pertence o Estádio da Luz?', options: ['Porto', 'Lisboa', 'Braga', 'Setúbal'], answer: 1 },
  { q: 'Qual é o ponto mais alto de Portugal continental?', options: ['Serra da Estrela', 'Serra do Gerês', 'Serra de Sintra', 'Serra de Montejunto'], answer: 0 },
  { q: 'Qual cidade portuguesa é conhecida como "Cidade Invicta"?', options: ['Lisboa', 'Coimbra', 'Porto', 'Braga'], answer: 2 },
  { q: 'Quantos Balões de Ouro tem Cristiano Ronaldo?', options: ['4', '5', '6', '7'], answer: 1 },
  { q: 'Em que ano Portugal aderiu à CEE (atual UE)?', options: ['1976', '1982', '1986', '1990'], answer: 2 },
  { q: 'Qual é o nome do parlamento português?', options: ['Senado', 'Assembleia da República', 'Cortes Gerais', 'Câmara dos Deputados'], answer: 1 },
  { q: 'Onde nasceu Fernando Pessoa?', options: ['Porto', 'Coimbra', 'Lisboa', 'Setúbal'], answer: 2 },
  { q: 'Qual é a bebida alcoólica típica do Alentejo?', options: ['Vinho Verde', 'Vinho do Porto', 'Medronho', 'Bagaço'], answer: 2 },
  // GEOGRAFIA MUNDIAL
  { q: 'Qual é o maior oceano do mundo?', options: ['Atlântico', 'Índico', 'Ártico', 'Pacífico'], answer: 3 },
  { q: 'Qual é a capital da Austrália?', options: ['Sydney', 'Melbourne', 'Camberra', 'Brisbane'], answer: 2 },
  { q: 'Qual é o país mais populoso do mundo?', options: ['China', 'Índia', 'EUA', 'Indonésia'], answer: 1 },
  { q: 'Qual é o maior país do mundo em área?', options: ['Canadá', 'EUA', 'China', 'Rússia'], answer: 3 },
  { q: 'Em que continente fica o Egipto?', options: ['Ásia', 'Europa', 'África', 'Médio Oriente'], answer: 2 },
  { q: 'Qual é a capital do Brasil?', options: ['Rio de Janeiro', 'São Paulo', 'Brasília', 'Salvador'], answer: 2 },
  { q: 'Qual é a montanha mais alta do mundo?', options: ['K2', 'Kilimanjaro', 'Monte Everest', 'Mont Blanc'], answer: 2 },
  { q: 'Qual é o rio mais longo do mundo?', options: ['Amazonas', 'Nilo', 'Yang-Tsé', 'Mississippi'], answer: 1 },
  { q: 'Qual é a capital do Japão?', options: ['Osaka', 'Tóquio', 'Kyoto', 'Hiroshima'], answer: 1 },
  { q: 'Qual é o menor país do mundo?', options: ['Mónaco', 'San Marino', 'Vaticano', 'Liechtenstein'], answer: 2 },
  { q: 'Qual é a capital da Argentina?', options: ['Buenos Aires', 'Montevideu', 'Santiago', 'Lima'], answer: 0 },
  { q: 'Em que país fica a Torre Eiffel?', options: ['Itália', 'Espanha', 'França', 'Bélgica'], answer: 2 },
  { q: 'Qual é o deserto maior do mundo?', options: ['Sahara', 'Gobi', 'Kalahari', 'Antártico'], answer: 3 },
  { q: 'Quantos países existem em África?', options: ['44', '50', '54', '60'], answer: 2 },
  { q: 'Qual é a capital da Noruega?', options: ['Estocolmo', 'Copenhaga', 'Oslo', 'Helsínquia'], answer: 2 },
  { q: 'Em que país fica o Machu Picchu?', options: ['Brasil', 'Colômbia', 'Chile', 'Peru'], answer: 3 },
  { q: 'Qual é o lago mais profundo do mundo?', options: ['Lago Superior', 'Lago Baikal', 'Lago Vitória', 'Mar Cáspio'], answer: 1 },
  { q: 'Qual é a capital da Índia?', options: ['Bombaim', 'Nova Deli', 'Calcutá', 'Bangalore'], answer: 1 },
  { q: 'Em que continente fica o Brasil?', options: ['América Central', 'América do Norte', 'América do Sul', 'Caraíbas'], answer: 2 },
  { q: 'Qual é a capital da China?', options: ['Xangai', 'Guangzhou', 'Pequim', 'Chengdu'], answer: 2 },
  // CIÊNCIA
  { q: 'Qual é o elemento químico representado por "Au"?', options: ['Prata', 'Alumínio', 'Ouro', 'Bronze'], answer: 2 },
  { q: 'Qual é a fórmula química da água?', options: ['CO2', 'H2O', 'O2', 'NaCl'], answer: 1 },
  { q: 'Quantos planetas tem o sistema solar?', options: ['7', '8', '9', '10'], answer: 1 },
  { q: 'Qual é o menor planeta do sistema solar?', options: ['Vénus', 'Marte', 'Mercúrio', 'Plutão'], answer: 2 },
  { q: 'O que estuda a ornitologia?', options: ['Insetos', 'Peixes', 'Aves', 'Répteis'], answer: 2 },
  { q: 'Qual é a unidade de medida da força?', options: ['Joule', 'Watt', 'Newton', 'Pascal'], answer: 2 },
  { q: 'Quantas pernas tem uma aranha?', options: ['6', '8', '10', '12'], answer: 1 },
  { q: 'Qual é o gás mais abundante na atmosfera terrestre?', options: ['Oxigénio', 'Dióxido de carbono', 'Azoto', 'Árgon'], answer: 2 },
  { q: 'Qual é o número atómico do oxigénio?', options: ['6', '7', '8', '9'], answer: 2 },
  { q: 'O que é a fotossíntese?', options: ['Digestão de luz', 'Produção de energia pela luz', 'Reprodução de plantas', 'Respiração noturna'], answer: 1 },
  { q: 'Qual animal tem o maior cérebro em relação ao corpo?', options: ['Elefante', 'Golfinho', 'Humano', 'Chimpanzé'], answer: 2 },
  { q: 'A que velocidade viaja a luz no vácuo?', options: ['200 000 km/s', '300 000 km/s', '150 000 km/s', '400 000 km/s'], answer: 1 },
  { q: 'Qual é o símbolo químico do ferro?', options: ['Fr', 'Fi', 'Fe', 'Fo'], answer: 2 },
  { q: 'Quantos cromossomas tem uma célula humana normal?', options: ['23', '44', '46', '48'], answer: 2 },
  { q: 'Qual é o osso mais longo do corpo humano?', options: ['Úmero', 'Rádio', 'Tíbia', 'Fémur'], answer: 3 },
  { q: 'Qual planeta é conhecido pelo anel?', options: ['Júpiter', 'Saturno', 'Úrano', 'Neptuno'], answer: 1 },
  { q: 'O que mede o sismógrafo?', options: ['Temperatura', 'Pressão', 'Terremotos', 'Humidade'], answer: 2 },
  { q: 'Qual é o metal mais condutor de eletricidade?', options: ['Ouro', 'Cobre', 'Prata', 'Alumínio'], answer: 2 },
  { q: 'Quantos litros de sangue tem um adulto?', options: ['3-4', '5-6', '7-8', '9-10'], answer: 1 },
  { q: 'Qual é o órgão mais pesado do corpo humano?', options: ['Coração', 'Pulmão', 'Fígado', 'Rim'], answer: 2 },
  // DESPORTO
  { q: 'Quantos jogadores tem uma equipa de basquetebol?', options: ['4', '5', '6', '7'], answer: 1 },
  { q: 'Quantas voltas tem o Tour de France?', options: ['15', '18', '21', '25'], answer: 2 },
  { q: 'Em que ano foi o primeiro Campeonato do Mundo de futebol?', options: ['1926', '1930', '1934', '1938'], answer: 1 },
  { q: 'Qual país ganhou mais Mundiais de futebol?', options: ['Alemanha', 'Argentina', 'Brasil', 'Itália'], answer: 2 },
  { q: 'Quantos sets tem um jogo de ténis (melhor de 5) para vencer?', options: ['2', '3', '4', '5'], answer: 1 },
  { q: 'Qual é o recorde do mundo dos 100m rasos masculino?', options: ['9,58s', '9,69s', '9,72s', '9,81s'], answer: 0 },
  { q: 'Quantos pontos vale um try no râguebi?', options: ['3', '4', '5', '7'], answer: 2 },
  { q: 'Em que desporto se usa o termo "birdie"?', options: ['Ténis', 'Golfe', 'Badminton', 'Squash'], answer: 1 },
  { q: 'Quantos Mundiais de futebol ganhou Portugal?', options: ['0', '1', '2', '3'], answer: 0 },
  { q: 'Onde se realizam os Jogos Olímpicos de verão de 2024?', options: ['Londres', 'Los Angeles', 'Paris', 'Berlim'], answer: 2 },
  { q: 'Qual é o desporto mais praticado no mundo?', options: ['Basquetebol', 'Futebol', 'Cricket', 'Ténis'], answer: 1 },
  { q: 'Quantos jogadores tem uma equipa de voleibol?', options: ['5', '6', '7', '8'], answer: 1 },
  { q: 'Quem detém o recorde de mais Grandes Slams no ténis masculino?', options: ['Rafael Nadal', 'Roger Federer', 'Novak Djokovic', 'Andy Murray'], answer: 2 },
  { q: 'Em que cidade se disputou o Mundial de 2022?', options: ['Dubai', 'Abu Dhabi', 'Riade', 'Doha'], answer: 3 },
  { q: 'Quantos jogadores tem uma equipa de futebol americano no campo?', options: ['9', '10', '11', '12'], answer: 2 },
  // CULTURA & ENTRETENIMENTO
  { q: 'Quem pintou a Mona Lisa?', options: ['Michelangelo', 'Raffaello', 'Leonardo da Vinci', 'Donatello'], answer: 2 },
  { q: 'Qual destes filmes ganhou mais Óscares?', options: ['Titanic', 'O Senhor dos Anéis: O Regresso do Rei', 'Ben-Hur', 'Todos os anteriores com 11'], answer: 3 },
  { q: 'Quem escreveu Harry Potter?', options: ['Stephenie Meyer', 'J.R.R. Tolkien', 'J.K. Rowling', 'C.S. Lewis'], answer: 2 },
  { q: 'Qual é o instrumento principal do jazz?', options: ['Guitarra', 'Violino', 'Saxofone', 'Trompete'], answer: 2 },
  { q: 'Em que ano foi lançado o primeiro iPhone?', options: ['2005', '2006', '2007', '2008'], answer: 2 },
  { q: 'Quem compôs a Quinta Sinfonia?', options: ['Mozart', 'Bach', 'Beethoven', 'Chopin'], answer: 2 },
  { q: 'Qual é a série mais vista da Netflix?', options: ['La Casa de Papel', 'Stranger Things', 'Squid Game', 'Ozark'], answer: 2 },
  { q: 'Quem é o autor de "Dom Quixote"?', options: ['Lope de Vega', 'Miguel de Cervantes', 'García Lorca', 'Pablo Neruda'], answer: 1 },
  { q: 'Qual é o personagem mais famoso de Sherlock Holmes?', options: ['Watson', 'Moriarty', 'Irene Adler', 'Sherlock Holmes'], answer: 3 },
  { q: 'Em que ano estreou o primeiro Star Wars?', options: ['1975', '1977', '1979', '1981'], answer: 1 },
  { q: 'Qual banda vendeu mais discos na história?', options: ['Rolling Stones', 'Led Zeppelin', 'The Beatles', 'Elvis Presley'], answer: 2 },
  { q: 'Quem pintou "A Noite Estrelada"?', options: ['Picasso', 'Monet', 'Van Gogh', 'Dalí'], answer: 2 },
  { q: 'Qual é o videojogo mais vendido de todos os tempos?', options: ['Tetris', 'Minecraft', 'GTA V', 'Super Mario Bros'], answer: 1 },
  { q: 'Quem escreveu "Crime e Castigo"?', options: ['Tolstói', 'Dostoiévski', 'Tchékhov', 'Turguêniev'], answer: 1 },
  { q: 'Em que país nasceu Mozart?', options: ['Alemanha', 'Suíça', 'Áustria', 'República Checa'], answer: 2 },
  // TECNOLOGIA
  { q: 'Quem fundou a Apple?', options: ['Bill Gates', 'Steve Jobs', 'Mark Zuckerberg', 'Elon Musk'], answer: 1 },
  { q: 'Qual é a menor unidade de informação digital?', options: ['Byte', 'Nibble', 'Bit', 'Kilobyte'], answer: 2 },
  { q: 'O que significa "HTML"?', options: ['High Transfer Machine Language', 'HyperText Markup Language', 'Hyper Terminal Machine Logic', 'High Text Markup Logic'], answer: 1 },
  { q: 'Em que ano foi fundada a Google?', options: ['1996', '1998', '2000', '2002'], answer: 1 },
  { q: 'Qual linguagem de programação é usada principalmente para web frontend?', options: ['Python', 'Java', 'JavaScript', 'C++'], answer: 2 },
  { q: 'O que é um "CPU"?', options: ['Unidade de Processamento Central', 'Unidade de Controlo de Programas', 'Circuito de Processamento Universal', 'Central Program Utility'], answer: 0 },
  { q: 'Quem inventou o telefone?', options: ['Thomas Edison', 'Nikola Tesla', 'Alexander Graham Bell', 'Guglielmo Marconi'], answer: 2 },
  { q: 'Qual empresa criou o sistema operativo Android?', options: ['Apple', 'Microsoft', 'Google', 'Samsung'], answer: 2 },
  { q: 'O que significa "Wi-Fi"?', options: ['Wireless Fidelity', 'Wide Frequency', 'Wireless Fiber', 'Web Interface'], answer: 0 },
  { q: 'Em que ano foi criado o Facebook?', options: ['2002', '2004', '2006', '2008'], answer: 1 },
  // HISTÓRIA MUNDIAL
  { q: 'Em que ano caiu o Muro de Berlim?', options: ['1987', '1988', '1989', '1991'], answer: 2 },
  { q: 'Quem foi o primeiro presidente dos EUA?', options: ['Abraham Lincoln', 'Thomas Jefferson', 'George Washington', 'Benjamin Franklin'], answer: 2 },
  { q: 'Em que ano começou a Primeira Guerra Mundial?', options: ['1912', '1914', '1916', '1918'], answer: 1 },
  { q: 'Quem foi Napoleão Bonaparte?', options: ['Rei de França', 'Imperador dos Franceses', 'General Inglês', 'Czar Russo'], answer: 1 },
  { q: 'Em que ano chegou o homem à Lua?', options: ['1967', '1968', '1969', '1970'], answer: 2 },
  { q: 'Quem foi o primeiro homem na Lua?', options: ['Buzz Aldrin', 'Neil Armstrong', 'Yuri Gagarin', 'John Glenn'], answer: 1 },
  { q: 'Em que país ocorreu a Revolução Francesa?', options: ['Inglaterra', 'Espanha', 'França', 'Itália'], answer: 2 },
  { q: 'Qual foi o primeiro animal a ir ao espaço?', options: ['Macaco', 'Cão', 'Rato', 'Gato'], answer: 1 },
  { q: 'Em que ano terminou a Segunda Guerra Mundial?', options: ['1943', '1944', '1945', '1946'], answer: 2 },
  { q: 'Qual foi a primeira civilização da Mesopotâmia?', options: ['Egípcia', 'Suméria', 'Persa', 'Babilónica'], answer: 1 },
  { q: 'Quem foi Nelson Mandela?', options: ['Presidente do Quénia', 'Primeiro-Ministro da Nigéria', 'Presidente da África do Sul', 'Líder do Zimbabué'], answer: 2 },
  { q: 'Em que ano foi a Revolução Russa?', options: ['1914', '1917', '1920', '1923'], answer: 1 },
  { q: 'Qual império era conhecido como "O Império onde o Sol nunca se põe"?', options: ['Romano', 'Espanhol', 'Britânico', 'Português'], answer: 2 },
  // NATUREZA & ANIMAIS
  { q: 'Qual é o animal terrestre mais rápido?', options: ['Leão', 'Tigre', 'Guepardo', 'Leopardo'], answer: 2 },
  { q: 'Qual é o maior animal do mundo?', options: ['Elefante africano', 'Baleia azul', 'Tubarão-baleia', 'Girafa'], answer: 1 },
  { q: 'Quantos dentes tem um adulto humano?', options: ['28', '30', '32', '34'], answer: 2 },
  { q: 'Qual é o único mamífero que voa?', options: ['Esquilo voador', 'Morcego', 'Ornitorrinco', 'Petauro'], answer: 1 },
  { q: 'De que se alimentam os koalas?', options: ['Bambu', 'Folhas de eucalipto', 'Erva', 'Frutos'], answer: 1 },
  { q: 'Quantas câmaras tem o coração de um mamífero?', options: ['2', '3', '4', '5'], answer: 2 },
  { q: 'Qual é o animal mais venenoso do mundo?', options: ['Cobra-rei', 'Medusa-caixa', 'Polvo-de-anéis-azuis', 'Escorpião'], answer: 1 },
  { q: 'Quantas espécies de pinguins existem?', options: ['8', '13', '18', '25'], answer: 2 },
  { q: 'Qual é a ave mais rápida do mundo?', options: ['Águia', 'Andorinhão', 'Falcão-peregrino', 'Albatroz'], answer: 2 },
  { q: 'Os golfinhos são:', options: ['Peixes', 'Anfíbios', 'Mamíferos', 'Répteis'], answer: 2 },
  // GASTRONOMIA
  { q: 'De que país é originário o sushi?', options: ['China', 'Coreia', 'Japão', 'Tailândia'], answer: 2 },
  { q: 'Qual é o ingrediente principal do guacamole?', options: ['Tomate', 'Abacate', 'Pimento', 'Cebola'], answer: 1 },
  { q: 'De onde é originária a pizza?', options: ['Espanha', 'Grécia', 'França', 'Itália'], answer: 3 },
  { q: 'O que é o "tempeh"?', options: ['Molho japonês', 'Alga marinha', 'Soja fermentada', 'Especiaria indiana'], answer: 2 },
  { q: 'Qual país consome mais café per capita?', options: ['Brasil', 'Itália', 'Finlândia', 'EUA'], answer: 2 },
  { q: 'De que fruto se faz o vinho?', options: ['Ameixa', 'Uva', 'Maçã', 'Pêra'], answer: 1 },
  { q: 'O que é o "kimchi"?', options: ['Sopa coreana', 'Legumes fermentados coreanos', 'Arroz frito japonês', 'Caril tailandês'], answer: 1 },
  { q: 'Qual é o queijo mais consumido no mundo?', options: ['Gouda', 'Cheddar', 'Mozzarella', 'Brie'], answer: 1 },
  { q: 'De que país é originário o chocolate?', options: ['Bélgica', 'Suíça', 'México (cacau)', 'França'], answer: 2 },
  { q: 'O que é o "foie gras"?', options: ['Queijo francês', 'Fígado gordo de pato ou ganso', 'Peixe defumado', 'Doce de frutos vermelhos'], answer: 1 },
  // MATEMÁTICA & LÓGICA
  { q: 'Quantos lados tem um hexágono?', options: ['5', '6', '7', '8'], answer: 1 },
  { q: 'Qual é a raiz quadrada de 144?', options: ['11', '12', '13', '14'], answer: 1 },
  { q: 'Quantos zeros tem um milhão?', options: ['5', '6', '7', '8'], answer: 1 },
  { q: 'Qual é o número Pi (aproximado)?', options: ['3,14', '3,16', '3,12', '3,18'], answer: 0 },
  { q: 'Quanto é 15% de 200?', options: ['20', '25', '30', '35'], answer: 2 },
  { q: 'Quantos graus tem um triângulo?', options: ['90', '180', '270', '360'], answer: 1 },
  { q: 'Qual é o número primo mais pequeno?', options: ['0', '1', '2', '3'], answer: 2 },
  { q: 'Quanto é 2 elevado a 10?', options: ['512', '1024', '2048', '256'], answer: 1 },
  { q: 'Quantos minutos tem um dia?', options: ['1200', '1440', '1600', '1800'], answer: 1 },
  { q: 'Qual é o resultado de 7 × 8?', options: ['54', '56', '58', '62'], answer: 1 },
  // MISCELÂNEA
  { q: 'Qual é a moeda oficial do Japão?', options: ['Won', 'Yuan', 'Yen', 'Ringgit'], answer: 2 },
  { q: 'Quantos continentes tem a Terra?', options: ['5', '6', '7', '8'], answer: 2 },
  { q: 'Qual é a língua mais falada no mundo?', options: ['Inglês', 'Espanhol', 'Mandarim', 'Hindi'], answer: 2 },
  { q: 'Em que ano foi fundada a ONU?', options: ['1943', '1945', '1947', '1950'], answer: 1 },
  { q: 'Qual é o nome científico do ser humano?', options: ['Homo sapiens', 'Homo erectus', 'Homo habilis', 'Pan troglodytes'], answer: 0 },
  { q: 'Quantas cordas tem uma guitarra standard?', options: ['4', '5', '6', '7'], answer: 2 },
  { q: 'Qual é a capital da Espanha?', options: ['Barcelona', 'Sevilha', 'Madrid', 'Valência'], answer: 2 },
  { q: 'De que material é feita a Estátua da Liberdade?', options: ['Ferro', 'Bronze', 'Cobre', 'Aço'], answer: 2 },
  { q: 'Quantos anos tem um mandato presidencial nos EUA?', options: ['3', '4', '5', '6'], answer: 1 },
  { q: 'Qual é a maior pirâmide do Egipto?', options: ['Quéfren', 'Miquerinos', 'Quéops', 'Djoser'], answer: 2 },
  { q: 'Qual o nome do satélite natural da Terra?', options: ['Io', 'Titã', 'Lua', 'Ganimedes'], answer: 2 },
  { q: 'Em que país fica Machu Picchu?', options: ['Chile', 'Argentina', 'Colômbia', 'Peru'], answer: 3 },
  { q: 'Qual é o metal mais precioso?', options: ['Ouro', 'Platina', 'Paládio', 'Ródio'], answer: 3 },
  { q: 'Quantas horas tem uma semana?', options: ['148', '168', '176', '192'], answer: 1 },
  { q: 'Qual é a cor resultante de misturar azul e amarelo?', options: ['Roxo', 'Laranja', 'Verde', 'Castanho'], answer: 2 },
  { q: 'Qual foi o primeiro país a dar o direito de voto às mulheres?', options: ['EUA', 'Reino Unido', 'Nova Zelândia', 'Suécia'], answer: 2 },
  { q: 'Quanto pesa aproximadamente o cérebro humano?', options: ['0,5 kg', '1 kg', '1,4 kg', '2 kg'], answer: 2 },
  { q: 'Qual é o instrumento de cordas mais grave?', options: ['Viola', 'Violoncelo', 'Contrabaixo', 'Harpa'], answer: 2 },
  { q: 'Qual é o país com mais lagos do mundo?', options: ['Rússia', 'EUA', 'Canadá', 'Finlândia'], answer: 2 },
  { q: 'Quantas asas tem uma abelha?', options: ['2', '4', '6', '8'], answer: 1 },
];

const TOTAL_ROUNDS = 10;
const TIME_LIMIT = 20;

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

module.exports = {
  init(session) {
    session.gameData.questions = shuffle(QUESTIONS).slice(0, TOTAL_ROUNDS);
    session.gameData.totalRounds = TOTAL_ROUNDS;
  },

  getRound(session) {
    const idx = session.round - 1;
    if (idx >= session.gameData.totalRounds) return null;
    const q = session.gameData.questions[idx];
    return {
      gameType: 'quiz',
      round: session.round,
      total: session.gameData.totalRounds,
      prompt: q.q,
      options: q.options,
      timeLimit: TIME_LIMIT,
      answerIndex: q.answer,
    };
  },

  onAnswer(session, player, answer, onAllAnswered) {
    if (!session.gameData.currentAnswers) session.gameData.currentAnswers = {};
    if (session.gameData.currentAnswers[player.name] != null) return;
    session.gameData.currentAnswers[player.name] = { answer, timestamp: Date.now() };
    const answered = Object.keys(session.gameData.currentAnswers).length;
    const total = session.players.length;
    if (session._io) {
      session._io.to(session.sessionId).emit('all_answered', { count: answered, total });
    }
    if (answered >= total) onAllAnswered();
  },

  scoreRound(session) {
    const q = session.gameData.questions[session.round - 1];
    const correctIndex = q.answer;
    const answers = session.gameData.currentAnswers || {};
    const correct = Object.entries(answers)
      .filter(([, v]) => v.answer === correctIndex)
      .sort(([, a], [, b]) => a.timestamp - b.timestamp);
    const pointsMap = [3, 2, 1];
    const deltas = [];
    session.players.forEach(p => {
      const entry = answers[p.name];
      if (!entry || entry.answer !== correctIndex) { deltas.push({ name: p.name, delta: 0 }); return; }
      const rank = correct.findIndex(([name]) => name === p.name);
      deltas.push({ name: p.name, delta: rank < pointsMap.length ? pointsMap[rank] : 1 });
    });
    return { correctIndex, correctText: q.options[correctIndex], answers: Object.fromEntries(Object.entries(answers).map(([n, v]) => [n, v.answer])), deltas };
  },
};
