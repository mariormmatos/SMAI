// Artista Relâmpago — server-side game logic

const PROMPTS = [
  // Nomes e slogans
  'Inventa um nome para um perfume feito para pessoas que trabalham de casa.',
  'Escreve o slogan de uma marca de pizza para astronautas.',
  'Dá um nome épico a uma loja de meias.',
  'Nomeia uma app de encontros para veganos extremistas.',
  'Cria o nome de uma música country sobre ficar preso no trânsito em Lisboa.',
  'Inventa o nome de um festival de música para pessoas que odeiam música alta.',
  'Dá um nome a uma banda de música formada por políticos portugueses.',
  'Inventa um slogan para vender areia no deserto.',
  'Cria o nome de uma linha de roupa para pessoas que nunca saem de casa.',
  'Dá um nome a um restaurante que só serve comida de hospital.',
  'Inventa o nome de uma academia de ginástica para pessoas preguiçosas.',
  'Cria um slogan para uma empresa que vende silêncio.',
  'Dá um nome a um perfume que cheira a segunda-feira de manhã.',
  'Inventa o nome de uma app que lembra as pessoas de respirar.',
  'Cria o nome de uma marca de almofadas para pessoas workaholic.',
  'Dá um nome a um café que só serve descafeinado.',
  'Inventa o nome de um museu dedicado exclusivamente a objetos perdidos.',
  'Cria um slogan para uma empresa de mudanças para pessoas indecisos.',
  'Dá um nome a um canal de YouTube de um pasteleiro que odeia açúcar.',
  'Inventa o nome de uma agência de viagens para pessoas que têm medo de viajar.',
  'Cria o nome de uma app de meditação para pessoas com TDAH.',
  'Dá um nome a uma marca de desodorizante para ursos polares.',
  'Inventa o slogan de uma escola de condução para idosos.',
  'Cria o nome de uma banda punk formada por avós portuguesas.',
  'Dá um nome a um spa exclusivo para polvos.',
  'Inventa o nome de uma empresa de seguros para gatos aventureiros.',
  'Cria um slogan para um ginásio que funciona só de madrugada.',
  'Dá um nome a uma série de documentários sobre pessoas que colecionam sacos de plástico.',
  'Inventa o nome de um partido político cujo único objetivo é que toda a gente durma mais.',
  'Cria o menu de um restaurante onde todos os pratos têm nomes de ex-presidentes.',
  'Dá um nome a uma app que avalia a qualidade do teu silêncio.',
  'Inventa um slogan para uma empresa que faz funerais temáticos.',
  'Cria o nome de uma loja que só vende produtos para pessoas com medo da escuridão.',
  'Dá um nome a um canal de ASMR de um mecânico.',
  'Inventa o nome de um serviço de entregas por pombos-correio moderno.',
  'Cria o slogan de uma agência de namoro para introvertidos.',
  'Dá um nome a um hotel onde tudo é feito de queijo.',
  'Inventa o nome de um reality show sobre pessoas a dobrar roupa.',
  'Cria o nome de uma linha de iogurtes para atletas de xadrez.',
  'Dá um nome a uma app onde podes contratar alguém para te dar más notícias.',
  'Inventa o nome de uma marca de meias que dura 200 anos.',
  'Cria um slogan para uma empresa de reparação de copos partidos.',
  'Dá um nome a um dicionário de palavras que só existem no Porto.',
  'Inventa o nome de uma série sobre um chef que só cozinha com microondas.',
  'Cria o slogan de uma empresa de táxis com cavalos.',
  'Dá um nome a um concurso de televisão onde as pessoas competem a fazer nada.',
  'Inventa o nome de um perfume que cheira a segunda-feira de manhã no metro.',
  'Cria o nome de um livro de autoajuda escrito por um procrastinador.',
  'Dá um nome a uma loja que só vende cousas que nunca se usam.',
  'Inventa o slogan de uma seguradora para ações de grupo.',
  'Cria o nome de uma app de dating para pessoas que odeiam tecnologia.',
  'Dá um nome a um festival de gastronomia de sobras de fim de semana.',
  'Inventa o nome de uma empresa que aluga personalidades.',
  'Cria um slogan para uma empresa que faz fila por ti.',
  'Dá um nome a um ginásio exclusivo para executivos que não têm tempo.',
  'Inventa o nome de um guia de viagens para pessoas que não querem sair de casa.',
  'Cria o nome de um reality show onde famosos competem a fingir que não são famosos.',
  'Dá um nome a um serviço de subscrição de desculpas prontas a usar.',
  'Inventa o slogan de uma empresa que fabrica buracos.',
  'Cria o nome de uma linha de roupa para pessoas que estão sempre com calor.',
  'Dá um nome a um café onde está proibido falar de trabalho.',
  'Inventa o nome de um serviço de babysitting para plantas.',
  'Cria um slogan para uma empresa de colchões para pessoas que não dormem.',
  'Dá um nome a um podcast sobre pessoas que têm medo de podcasts.',
  'Inventa o nome de uma marca de água com sabor a nada.',
  'Cria o nome de um museu de coisas que toda a gente tem em casa mas ninguém usa.',
  'Dá um nome a uma empresa de consultoria para pessoas que já sabem tudo.',
  'Inventa o slogan de um supermercado que só vende alimentos de cor amarela.',
  'Cria o nome de uma linha de produtos de beleza para cactus.',
  'Dá um nome a um serviço de fotografia para selfies de grupo onde ninguém fica bem.',
  'Inventa o nome de uma empresa que cria desculpas personalizadas por encomenda.',
  'Cria o slogan de uma companhia aérea low-cost que não inclui nada.',
  'Dá um nome a um spa temático de segunda-feira de manhã.',
  'Inventa o nome de uma escola de culinária para pessoas que só sabem fazer ovos.',
  'Cria o nome de um serviço de tradução de silêncios incómodos.',
  'Dá um nome a uma empresa que organiza despedidas de solteiro para introvertidos.',
  'Inventa o slogan de uma marca de chocolate para pessoas em dieta.',
  'Cria o nome de um canal de streaming que só transmite chuva.',
  'Cria o slogan de um hotel que só tem quartos minúsculos.',
  'Dá um nome a uma linha de cosméticos feita com lágrimas de crocodilo.',
  'Inventa o nome de um reality show sobre contabilistas em férias.',
  'Cria um slogan para um serviço de entrega de abraços.',
  // Títulos e bios
  'Dá um título a um filme sobre um gato que descobre a Internet.',
  'Cria o título de um livro sobre o tédio do trabalho em escritório.',
  'Escreve a sinopse de um romance histórico que nunca conseguiria ser publicado.',
  'Escreve a bio de Instagram de um crocodilo influencer.',
  'Dá um título a um documentário sobre pessoas que coleccionam tampas de garrafa.',
  'Cria o título de um livro de autoajuda completamente inútil.',
  'Escreve a bio de LinkedIn de um pirata reformado.',
  'Dá um título a uma série sobre um detetive que só resolve casos relacionados com comida.',
  'Cria o título de um livro de receitas para pessoas que odeiam cozinhar.',
  'Escreve a bio de Twitter de um fantasma moderno.',
  'Dá um título a um podcast sobre pessoas que falam com as suas plantas.',
  'Cria a sinopse de um filme de terror sobre impressoras de escritório.',
  'Escreve a bio de Instagram de uma pedra famosa.',
  'Dá um título a um livro de memórias escrito por uma cadeira de escritório.',
  'Cria o título de um livro sobre a história secreta dos semáforos.',
  'Escreve o resumo de um TED Talk sobre a importância de não fazer nada.',
  'Dá um título a uma série de animação sobre burocratas em Portugal.',
  'Cria o título de um livro de poesia escrito por uma máquina de vending.',
  'Escreve a bio de Instagram de uma nuvem com complexo de superioridade.',
  'Dá um título a um filme sobre uma inteligência artificial que só quer fazer siestas.',
  // Leis e regras imaginárias
  'Inventa uma lei estranha que faria sentido no séc. XXII.',
  'Inventa uma matéria escolar que deveria existir mas não existe.',
  'Cria uma regra absurda para um jogo de futebol que tornaria o desporto mais interessante.',
  'Inventa uma lei que proíbe algo completamente inofensivo mas irritante.',
  'Cria as regras de um desporto completamente inventado que só pode ser praticado em Portugal.',
  'Inventa uma disciplina obrigatória no secundário que os jovens de hoje precisariam.',
  'Cria uma lei que obriga todos os políticos a fazer algo humilhante.',
  'Inventa uma norma da EU completamente absurda mas que parece real.',
  'Cria a regra mais estranha possível para um clube de leitura.',
  'Inventa uma lei de trânsito que tornaria Lisboa ainda mais caótica.',
  // Descrições e explicações criativas
  'Inventa um nome para um superpoder completamente inútil.',
  'Escreve uma frase motivacional completamente absurda.',
  'Inventa a senha de entrada de um clube secreto de reformados.',
  'Descreve o sabor de uma gelatina de queijo em 1 frase.',
  'Descreve o WiFi do inferno em 1 frase.',
  'Inventa uma profissão do futuro que vai existir nos próximos 10 anos.',
  'Descreve o "prato do dia" de um restaurante num aeroporto às 3 da manhã.',
  'Escreve a mensagem de erro de uma app de meditação que crashou.',
  'Descreve como seria o cheiro de uma segunda-feira de manhã em 1 frase.',
  'Inventa uma desculpa completamente absurda para chegar atrasado ao trabalho.',
  'Descreve o paraíso para alguém que adora reuniões de trabalho.',
  'Inventa um superpoder que parece útil mas na prática é inútil.',
  'Descreve como seria um dia normal na vida de um polvo profissional.',
  'Escreve uma crítica negativa de 1 estrela sobre o sol.',
  'Descreve a sensação de pisar um Lego de noite sem usar palavrões.',
  'Inventa a notícia mais chocante que poderia aparecer no Jornal Nacional.',
  'Descreve como soa o silêncio em 5 palavras.',
  'Escreve um aviso de segurança para um elevador que só sobe.',
  'Descreve o que aconteceria se o WhatsApp deixasse de funcionar em Portugal.',
  'Inventa uma teoria da conspiração completamente inofensiva sobre os pastéis de nata.',
  'Descreve como seria uma crise diplomática entre Portugal e o Brasil por causa do sotaque.',
  'Escreve a letra do hino nacional de um país imaginário de pessoas indecisos.',
  'Inventa a primeira lei que passarias se fosses presidente por um dia.',
  'Descreve como seria um Natal num planeta sem inverno.',
  'Escreve as instruções de uso de uma máquina do tempo para principiantes.',
  'Inventa a desculpa que um fantasma usaria para não aparecer ao trabalho.',
  'Descreve o que os cães pensam realmente quando fingem que não ouviram.',
  'Escreve a mensagem numa garrafa lançada ao mar por um robot.',
  'Inventa o argumento mais absurdo que dois pombos teriam numa praça.',
  'Descreve como seria a Black Friday se fosse organizada por portugueses.',
  'Escreve a mensagem de boas-vindas de um hotel para viajantes no tempo.',
  // Mais nomes e slogans
  'Cria o nome de uma empresa de transporte de surpresas desagradáveis.',
  'Dá um nome a uma loja que vende coisas que ninguém precisa.',
  'Inventa o nome de um aplicativo para ajudar pessoas a fingir que estão ocupadas.',
  'Cria um slogan para uma marca de pijamas para trabalhadores em teletrabalho.',
  'Dá um nome a um clube exclusivo para pessoas que nunca terminam o que começam.',
  'Inventa o nome de uma empresa que organiza férias em zonas de obras.',
  'Cria o slogan de um dentista que tem muito medo de dentes.',
  'Dá um nome a uma linha de produtos de beleza para pessoas que dormem pouco.',
  'Inventa o nome de um festival gastronómico dedicado exclusivamente a tostas.',
  'Cria o nome de uma empresa de segurança especializada em proteger meias solitárias.',
  // Mais titles
  'Dá um título a um livro de autoajuda para pessoas que adoram reclamar.',
  'Cria o título de um filme de ação protagonizado por um reformado português.',
  'Escreve a sinopse de uma série sobre uma família que vive num parque de estacionamento.',
  'Dá um título a um documentário sobre o misterioso desaparecimento das canetas Bic.',
  'Cria o título de um livro de filosofia escrito por uma galinha.',
  'Escreve a bio de Instagram de um pinguim que se acha muito cool.',
  'Dá um título a um musical sobre finanças pessoais.',
  'Cria a sinopse de um thriller sobre o dia em que os semáforos ficaram todos a verde.',
  'Escreve o resumo de um livro de conselhos de um homem que nunca saiu da sua aldeia.',
  'Dá um título a um reality show onde pessoas competem para ser o mais normal possível.',
  // Inventos e criações absurdas
  'Inventa um aparelho doméstico completamente inútil mas que toda a gente iria querer.',
  'Cria um produto de cozinha que resolve um problema que ninguém tinha.',
  'Inventa um veículo de transporte absurdo mas que faria sentido em Lisboa.',
  'Cria um tipo de yoga completamente inventado.',
  'Inventa um jogo de tabuleiro que seria absolutamente frustrante de jogar.',
  'Cria um tipo de dieta que seria impossível de seguir.',
  'Inventa um gadget tecnológico que só funciona em condições muito específicas.',
  'Cria uma app para smartphones que só funciona se o utilizador estiver entediado.',
  'Inventa um serviço de assinatura mensal completamente absurdo.',
  'Cria um tipo de seguro para situações que nunca acontecem.',
  'Inventa um acessório de moda para reuniões de trabalho em formato de zoom.',
  'Cria um desporto aquático que só pode ser praticado em piscinas rasas.',
  'Inventa um tipo de turismo para pessoas que odeiam as pessoas.',
  'Cria um aplicativo de dating baseado exclusivamente no tipo de pizza favorito.',
  'Inventa uma forma de transporte público que seria pior do que o metro de Lisboa.',
  // Personagens e situações imaginárias
  'Escreve o perfil de Tinder de um vampiro moderno que vive no Algarve.',
  'Cria o curriculum vitae de um dragão que quer trabalhar em recursos humanos.',
  'Inventa o discurso de candidatura de um alien que quer ser presidente de câmara.',
  'Escreve a carta de apresentação de um fantasma para um emprego em segurança.',
  'Cria o plano de negócios de uma empresa gerida por gatos.',
  'Escreve o manual de instruções de um robô que só faz o que quer.',
  'Inventa o testemunho de um turista que visitou Portugal pela primeira vez.',
  'Cria o discurso de despedida de um funcionário público que trabalhou 40 anos sem fazer nada.',
  'Escreve a review de um restaurant por alguém que nunca comeu comida portuguesa.',
  'Inventa a carta de reclamação de um fantasma ao condomínio.',
  'Cria a entrevista de um unicórnio para um emprego num banco.',
  'Escreve o relatório anual de um detetive que só investigou casos de meias desaparecidas.',
  'Inventa o testamento de alguém que só tem coisas sem valor.',
  'Cria o diário de bordo de um pirata que navega no Tejo.',
  'Escreve a carta de amor de um robot à sua impressora favorita.',
  // Desafios de imaginação
  'Se os animais tivessem sindicatos, qual seria a primeira greve a acontecer e porquê?',
  'Inventa um novo feriado nacional português e justifica a sua existência.',
  'Se o pastel de nata tivesse um agente literário, que tipo de contratos assinaria?',
  'Cria o manifesto político de um partido dedicado exclusivamente a melhorar as filas de espera.',
  'Inventa a conversa que dois buracos no pavimento de Lisboa teriam entre si.',
  'Se os elétricos de Lisboa falassem, o que diriam aos turistas?',
  'Inventa a desculpa do Estado Português para não arranjar as estradas.',
  'Cria o roteiro de uma viagem de fim de semana a Portugal escrito por alguém que nunca saiu do Brasil.',
  'Inventa a conversa que um prego e uma tábua teriam numa carpintaria.',
  'Escreve o relatório meteorológico de um dia em Lisboa descrito por alguém que odeia Lisboa.',
  'Se as chouriças tivessem sindicatos, qual seria a sua principal reivindicação?',
  'Inventa a letra de um fado sobre a dificuldade de fazer download de ficheiros grandes.',
  'Cria o itinerário de férias perfeito para alguém que odeia tudo.',
  'Escreve o contrato de trabalho de um gnomo de jardim.',
  'Inventa a história de origem do pastel de Belém numa versão de ficção científica.',
  // Mais descrições absurdas
  'Descreve o sabor do azul em termos gastronómicos.',
  'Explica o conceito de segunda-feira a um alienígena que nunca ouviu falar de trabalho.',
  'Descreve como seria o mundo se os pombos fossem os seres dominantes.',
  'Explica por que razão as meias desaparecem na máquina de lavar usando uma teoria científica.',
  'Descreve o que acontece no céu quando chove em Lisboa.',
  'Explica o trânsito de Lisboa a alguém que nunca ouviu falar de caos.',
  'Descreve como seria um dia normal para alguém com o superpoder de entender o IKEA.',
  'Explica o fenómeno de não conseguir decidir o que comer usando linguagem académica.',
  'Descreve o que os gatos pensam realmente quando nos ignoram.',
  'Explica o conceito de siesta a alguém de um país frio.',
  'Descreve o cheiro de uma reunião de trabalho que podia ter sido um email.',
  'Explica por que razão as obras em Portugal demoram sempre o triplo do previsto.',
  'Descreve o som que o silêncio faz depois de uma festa portuguesa.',
  'Explica o fenómeno de fazer scroll infinito no telemóvel em linguagem poética.',
  'Descreve como seria o sabor da procrastinação.',
  // Ainda mais criatividade
  'Inventa um dialeto português novo para usar apenas em supermercados.',
  'Cria as regras de um clube secreto de pessoas que adoram ficar em casa.',
  'Inventa um ritual matinal absurdo que toda a gente deveria fazer.',
  'Cria o juramento de fidelidade de uma organização dedicada à proteção dos pastéis de nata.',
  'Inventa o código de conduta de um grupo de WhatsApp de família.',
  'Cria as regras de um desporto que só pode ser jogado em elevadores.',
  'Inventa um sistema monetário alternativo baseado em pastéis.',
  'Cria o curriculum da pessoa mais inútil do mundo mas que é excelente em coisas inúteis.',
  'Inventa o discurso do Ano Novo de um presidente completamente honesto.',
  'Cria a letra de uma música de embalar para adultos stressados.',
  'Inventa o hino de um bairro de Lisboa escrito no estilo dos anos 80.',
  'Cria um tour gastronómico de Portugal explicado por alguém que odeia comer.',
  'Inventa as instruções de montagem de uma estante do IKEA escritas por um filósofo.',
  'Cria um poema sobre a dificuldade de encontrar estacionamento em Lisboa.',
  'Inventa a mensagem de correio de voz de alguém que não quer que ninguém ligue.',
  'Cria o guia de sobrevivência para um primeiro dia de trabalho numa repartição pública.',
  'Inventa o roteiro da pior lua de mel possível.',
  'Cria a descrição de produto de algo que toda a gente tem mas ninguém quer.',
  'Inventa o manifesto de uma pessoa que quer abolir as segundas-feiras.',
  'Cria o discurso de aceitação de um prémio por ser a pessoa mais medíocre do ano.',
  // Situações sociais e tecnológicas
  'Inventa a notificação mais irritante que um telemóvel poderia enviar.',
  'Cria o texto de uma mensagem de grupo que causaria caos total na família.',
  'Inventa uma razão histórica completamente falsa para o horário de verão.',
  'Cria a política de privacidade de um aplicativo que espiona as tuas meias.',
  'Inventa os termos e condições de um contrato com um génio da lâmpada.',
  'Cria o manual do utilizador de um ser humano com bugs frequentes.',
  'Inventa a mensagem automática de ausência de alguém que está ausente para sempre.',
  'Cria as FAQs de um serviço de atendimento ao cliente de uma empresa de fantasmas.',
  'Inventa o texto de uma publicidade para algo que ninguém precisa mas toda a gente iria comprar.',
  'Cria a história de erro 404 de um site de receitas portuguesas.',
  'Inventa uma password extremamente complicada que ninguém ia esquecer.',
  'Cria a notificação de push mais inútil que uma app poderia mandar.',
  'Inventa a mensagem de confirmação de subscrição de uma newsletter que ninguém pediu.',
  'Cria o texto de uma crítica online de 1 estrela à existência humana.',
  'Inventa a resposta automática de um robô de atendimento que claramente não quer ajudar.',
  // Mais situações e personagens
  'Escreve a carta de demissão de um funcionário público que nunca trabalhou de facto.',
  'Inventa o discurso de abertura de uma loja que vende produtos completamente inúteis.',
  'Cria o slogan de uma empresa que promete ser a segunda melhor em tudo.',
  'Escreve a crítica gastronómica de uma cantina de escola escrita por um crítico pretensioso.',
  'Inventa o manifesto de um partido político dedicado exclusivamente à proteção das siestas.',
  'Cria o resumo de currículo de alguém que passou 10 anos a ver séries.',
  'Escreve a mensagem de motivação de um treinador que acredita que perder é bom.',
  'Inventa o discurso de investidura de um presidente que foi eleito por engano.',
  'Cria o contrato de arrendamento de uma casa assombrada.',
  'Escreve o guia turístico de uma cidade que não existe mas devia existir.',
  'Inventa o menu de um restaurante onde o chef é daltónico.',
  'Cria a letra de uma canção de Natal para pessoas que odeiam o Natal.',
  'Escreve as instruções de primeiros socorros para uma maratona de séries.',
  'Inventa o código de ética de uma agência de espiões completamente incompetente.',
  'Cria o relatório anual de uma empresa que não fez nada durante o ano.',
  'Escreve a previsão do tempo de um meteorologista que nunca acerta.',
  'Inventa os votos de casamento de dois robots.',
  'Cria o guia de etiqueta para jantar em família portuguesa no Natal.',
  'Escreve a carta de candidatura de uma pessoa que quer ser o primeiro Ministro das Siestas.',
  'Inventa o comunicado de imprensa de uma empresa que descobriu como engarrafar entusiasmo.',
  'Cria o roteiro de um filme de suspense sobre uma impressora que decide rebelar-se.',
  'Escreve a letra de um fado sobre a dificuldade de encontrar estacionamento.',
  'Inventa as instruções de utilização de um carro voador para o condutor médio português.',
  'Cria a agenda de um dia na vida de um pato que trabalha como consultor.',
  'Escreve o depoimento de alguém que foi abduzido por aliens e ficou decepcionado.',
  'Inventa o plano de evacuação de emergência para uma fábrica de suspiros.',
  'Cria a lista de ingredientes de uma receita que nunca resultaria bem.',
  'Escreve o comunicado de uma empresa aérea que só voa em dias de sol.',
  'Inventa o programa de um festival de cinema dedicado exclusivamente a filmes sobre meias.',
  'Cria o discurso de um candidato a vereador que só quer melhorar as pastelarias.',
  // Mais criatividade
  'Escreve o horóscopo de amanhã para alguém que não acredita em horóscopos.',
  'Inventa o nome de um cocktail criado especialmente para reuniões de condomínio.',
  'Cria o slogan de uma campanha de saúde pública sobre os perigos de não fazer nada.',
  'Escreve a crítica de um livro que nunca existiu mas que soa muito interessante.',
  'Inventa o nome de um museu dedicado às coisas que nunca deviam ter sido inventadas.',
  'Cria o manifesto de um clube de pessoas que acham que tudo devia ser mais simples.',
  'Escreve a letra de uma canção pop sobre a alegria de encontrar uma ficha de tomada.',
  'Inventa o roteiro de uma telenovela passada num serviço de finanças.',
  'Cria o programa de um congresso científico sobre as propriedades mágicas das toucas de banho.',
  'Escreve as regras de um jogo de cartas baseado exclusivamente em desculpas.',
  'Inventa o script de uma publicidade para um produto que as pessoas já têm mas não sabem.',
  'Cria o testemunho de alguém que passou 30 dias sem abrir o telemóvel e sobreviveu.',
  'Escreve a sinopse de uma série documental sobre as guerras secretas entre vizinhos.',
  'Inventa o nome de um prémio literário para o livro mais aborrecido do ano.',
  'Cria o depoimento de um semáforo que viu coisas que não pode esquecer.',
  'Escreve a carta aberta de um sofá que pede para ser descansado de vez em quando.',
  'Inventa o hino de uma nação fundada no fundo do mar por caranguejos.',
  'Cria o manual de instruções para ser um português típico.',
  'Escreve a carta de apresentação de alguém que quer ser o personagem mais inútil de uma série.',
  'Inventa o programa de um cruzeiro temático dedicado exclusivamente a pessoas que adoram o silêncio.',
  'Cria o roteiro do pior filme de Natal alguma vez realizado.',
  'Escreve a descrição de um quadro abstrato pintado por um cão.',
  'Inventa o texto de uma placa comemorativa dedicada ao inventor do botão "adiar" do despertador.',
  'Cria o comunicado oficial do governo a explicar por que razão vai chover sempre no primeiro dia de férias.',
  'Escreve o manual de sobrevivência para trabalhar num open space português.',
  'Inventa a dedicatória de um livro escrito por alguém que não gosta de ninguém.',
  'Cria o guia do perfeito hóspede de casa de um português.',
  'Escreve as instruções de montagem de uma relação amorosa segundo o manual IKEA.',
  'Inventa o contrato social de uma família que decidiu criar as suas próprias regras.',
  'Cria o relatório de estágio de um estagiário que não aprendeu absolutamente nada.',
  'Escreve o obituário de uma segunda-feira.',
  'Inventa o testamento de alguém que só tinha dívidas e amor para dar.',
  'Cria o roteiro de viagem para o pior fim de semana alguma vez planeado.',
  'Escreve a ata de uma reunião que não devia ter existido.',
  'Inventa o contrato de um músico de rua que quer negociar as condições de atuação.',
  'Cria a carta de reclamação de um turista que foi a Portugal esperando clima temperado.',
  'Escreve o discurso de abertura de um museu dedicado ao orgulho local excessivo.',
  'Inventa a lista de regras de uma associação de pessoas que fingem que tudo está bem.',
  'Cria o manual de boas práticas para ser um avô português completo.',
  'Escreve o comunicado de imprensa de um clube de futebol que decide abolir os golos.',
  'Inventa a ementa de um restaurante especializado em comida de cantina universitária gourmet.',
  'Cria o guia de uso correto de uma palavra que ninguém sabe usar bem.',
  'Escreve a sinopse de um filme sobre as aventuras de um telecomando perdido.',
  'Inventa a canção tema de um elevador que tem medo de alturas.',
  'Cria o programa de treino de um atleta olímpico de procrastinação.',
  'Escreve a letra de uma canção de embalar sobre os perigos da internet.',
  'Inventa o guia gastronómico de Portugal para vegetarianos corajosos.',
  'Cria o roteiro de um documentário sobre as tribos secretas de Alfama.',
  'Escreve a lista de desejos de Natal de alguém que já tem tudo.',
  'Inventa a mensagem que alguém deixaria gravada para as gerações futuras numa cápsula do tempo.',
  'Cria o discurso de encerramento de um evento que nunca devia ter começado.',
  'Escreve o regulamento de uma competição de olhar para o teto.',
  'Inventa o programa de um retiro espiritual para pessoas que não acreditam em nada.',
  'Cria o guia de comunicação não-violenta para grupos de WhatsApp de família.',
  'Escreve a crítica de teatro de uma peça sobre pessoas que não conseguem tomar decisões.',
  'Inventa o nome de um reality show onde as pessoas competem para ser as mais organizadas.',
  'Cria a carta de amor de um Portugal imaginário a um Brasil imaginário.',
  'Escreve o discurso de motivação de um guru que não tem a certeza do que está a dizer.',
  'Inventa o regulamento de uma corrida de velocidade em câmara lenta.',
  'Cria o slogan de uma empresa de consultoria que cobra muito e faz pouco.',
  'Escreve a sinopse de um livro sobre alguém que tenta aprender a dançar kizomba sem jeito nenhum.',
  'Inventa o nome de um novo partido político cujo único objetivo é melhorar as filas nos correios.',
  'Cria o guia definitivo para sobreviver a um jantar de Natal com toda a família.',
  'Escreve a carta de um viajante do futuro que veio ao nosso tempo e ficou confuso com tudo.',
];

const TOTAL_ROUNDS = 5;
const TIME_LIMIT_WRITE = 60;
const TIME_LIMIT_VOTE = 20;

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
    session.gameData.prompts = shuffle(PROMPTS).slice(0, TOTAL_ROUNDS);
    session.gameData.totalRounds = TOTAL_ROUNDS;
    session.gameData.phase = 'write';
  },

  getRound(session) {
    const idx = session.round - 1;
    if (idx >= session.gameData.totalRounds) return null;
    session.gameData.phase = 'write';
    session.gameData.currentAnswers = {};
    session.gameData.currentVotes = {};
    session.gameData.answerOrder = null;
    return {
      gameType: 'creative',
      round: session.round,
      total: session.gameData.totalRounds,
      prompt: session.gameData.prompts[idx],
      timeLimit: TIME_LIMIT_WRITE,
      phase: 'write',
    };
  },

  onAnswer(session, player, answer, onAllAnswered) {
    if (session.gameData.phase !== 'write') return;
    if (session.gameData.currentAnswers[player.name] != null) return;
    session.gameData.currentAnswers[player.name] = answer.trim().substring(0, 200);

    const answered = Object.keys(session.gameData.currentAnswers).length;
    if (answered >= session.players.length) {
      // Start voting phase
      const items = shuffle(
        Object.entries(session.gameData.currentAnswers).map(([name, text]) => ({ name, text }))
      );
      session.gameData.answerOrder = items;
      session.gameData.phase = 'vote';
      if (session._io) {
        session._io.to(session.sessionId).emit('voting_start', {
          gameType: 'creative',
          items,
          timeLimit: TIME_LIMIT_VOTE,
          phase: 'vote',
        });
      }
    }
  },

  onVote(session, player, vote, onAllAnswered) {
    if (session.gameData.phase !== 'vote') return;
    if (session.gameData.currentVotes[player.name] != null) return;
    // vote = name of the player they voted for
    // can't vote for yourself
    if (vote === player.name) return;
    session.gameData.currentVotes[player.name] = vote;

    const voted = Object.keys(session.gameData.currentVotes).length;
    if (voted >= session.players.length) {
      onAllAnswered();
    }
  },

  scoreRound(session) {
    const votes = session.gameData.currentVotes;
    const voteTally = {};

    // Count votes per player
    Object.values(votes).forEach(targetName => {
      voteTally[targetName] = (voteTally[targetName] || 0) + 1;
    });

    // Sort by votes
    const ranked = Object.entries(voteTally).sort(([, a], [, b]) => b - a);
    const deltas = [];
    session.players.forEach(p => {
      const v = voteTally[p.name] || 0;
      let pts = 0;
      if (ranked[0] && ranked[0][0] === p.name) pts = 3;
      else if (ranked[1] && ranked[1][0] === p.name) pts = 1;
      deltas.push({ name: p.name, delta: pts });
    });

    return {
      votes: voteTally,
      answers: session.gameData.currentAnswers,
      answerOrder: session.gameData.answerOrder,
      deltas,
    };
  },
};
