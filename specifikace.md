Pokud je požadováno přemístění nákladu z jednoho místa do druhého, vozík si materiál vyzvedne do 1 minuty.

 - UNSPECIFIED_SUBJECT, Je nejednoznačné, jestli je náklad a materiál jedno a to samé. (materiál -> náklad)
 - UNSPECIFIED_SUBJECT, "Místo" je příliš obecné (místo -> stanice). 
 - OMISSION, Chybí důsledek, co se stane když si vozík vyzvedne náklad od 1 minuty?
 - RANDOM_STATEMENT, Kde si vozík materiál vyzvedne? (2 místa kam může jet)
 - IMPLICIT, Specifikovat že "požadavek" mí specifický účel.
 - AMB_TEMPORAL, Od čeho se začne počítat 1 minuta.

*Pokud dojde k přijetí požadavku vozíkem na přemístění nákladu ze zdrojové nakládací stanice do cílové nakládací stanice a vozík si tento náklad vyzvedne z počáteční stanice do 1 minuty od přijetí požadavku, tak dojde k naložení nákladu na vozík.*

Pokud se to nestihne, materiálu se nastavuje prioritní vlastnost.

 - UNSPECIFIED_SUBJECT, Přepsání výrazu materiál na náklad, pro sjednocení s celým textem. (materiál -> náklad)
 - AMB_REFERENCE, Pokud se co stane? Na co "to" odkazuje?
 - IMPLICIT, Není přesně stanovena priorita na co. Čeho se priorita týká.
 
*Pokud není náklad vyzvednut do 1 minuty od přijeti požadavku vozíkem, nákladu se nastaví prioritní vyřizování požadavku pro vyzvednutí nákladu.*

Každý prioritní materiál musí být vyzvednutý vozíkem do 1 minuty od nastavení prioritního požadavku.

 - DANGLING_ELSE, Když se něco MUSÍ stát, mělo by být jasné co se stane v případě když se to nestane. (chybí else)
 - UNSPECIFIED_SUBJECT, Přepsání výrazu materiál na náklad, pro sjednocení s celým textem. (materiál -> náklad)
 - OMISSION, Chybí důsledek. Co když do 1 minuty je náklad vyzvednut.
 - AMB_SUBJECT, Je prioritní materiál to stejné jako materiál s prioritním požadavkem pro vyzvednutí?
 - IMPLICIT, Mělo by být specifikované že "prioritní požadavek" je prioritní požadavek na vyzvednutí.
  
*Pokud je náklad vyzvednutý vozíkem do 1 minuty od nastavení prioritního požadavku pro vyzvednutí nákladu, tak se náklad naloží na daný vozík, jinak dojde k odstranení požadavku.*

Pokud vozík nakládá prioritní materiál, přepíná se do režimu pouze-vykládka. 

 - DANGLING_ELSE, Co se stane s nákledem, který nemá prioritu požadavku na naložení? (chybí else)
 - UNSPECIFIED_SUBJECT, Přepsání výrazu materiál na náklad, pro sjednocení s celým textem. (materiál -> náklad)
 - AMB_SUBJECT, Opět, je prioritní materiál to stejné jako materiál s prioritním požadavkem pro vyzvednutí?
 - AMB_STATEMENT, Má řežim "pouze-vykládka" jenom když nakládá ? co když skončí? 

*Pokud vozík nakládá náklad s prioritním vyřízením požadavku pro vyzvednutí, tak se přepne do režimu pouze-vykládka, jinak se vozík nepřepne do režimu pouze-vykládka*

V tomto režimu zustává, dokud nevyloží všechen takový materiál.

 - UNSPECIFIED_SUBJECT, Přepsání výrazu materiál na náklad, pro sjednocení s celým textem. (materiál -> náklad)
 - UNSPECIFIED_SUBJECT, Kdo v tomto režimu zůstává? (Mohlo by být více objektů s režimy a možností vykládat třeba jeřáb)
 - UNSPECIFIED_SUBJECT, "Takový" je hodně nespecifické, může to být prakticky jakýkoliv materiál.
 - AMB_SUBJECT, "Režim" je málo specifikovaný. Vozík může mít i více režimů.

*V režimu pouze-vykládka vozík zůstává, dokud nevyloží veškerý náklad, který má prioritní požadavek na vyzvednutí.*

Normálně vozík během své jízdy muže nabírat a vykládat další materiály v jiných zastávkách. 

 - DANGLING_ELSE, chybí else pro stav kdy je vozík v režimu pouze-vykládka.
 - UNSPECIFIED_SUBJECT, Opět je zde nejednotnost místa naložení/vyložení (zastávka -> stanice)
 - UNSPECIFIED_SUBJECT, Přepsání výrazu materiál na náklad, pro sjednocení s celým textem. (materiál -> náklad)
 - AMB_SUBJECT, "další materiály" může mít více významů. Např.: více množství nějákého materiálu nebo naložení dalšiho druhu materiálu atd.
 - AMB_STATEMENT, Věta zní jako, že vozík nemůže nakládat a vykládat náklad ve stejné stanici.
 - IMPLICIT, Vozík může něco dělat i nenormálně? Je zde myšlen stav kdy vozík není v režimu "pouze-vykládka".

*Pokud je vozík v režimu pouze-vykládka, tak vozík jede pouze do své cílové stanice, která je určena nákladem, který má prioritní požadavek na naložení, jinak vozík během své jízdy může nakládat a vykládat náklad ve stanicích, které se vyskytují po cestě dané jízdy.*

Na jednom míste muže vozík akceptovat nebo vyložit jeden i více materiálů. 

 - UNSPECIFIED_SUBJECT, "Místo" je nekonzistentní se zbytkem textu a je málo specifické. (místo -> stanice)
 - UNSPECIFIED_SUBJECT, Přepsání výrazu "materiál" na "náklad", pro sjednocení s celým textem. (materiál -> náklad)
 - AMB_SUBJECT, "nebo" zní jako že na jednom míste může vozík buď jenom naložit nebo jenom vyložit náklad.
 - AMB_STATEMENT, "akceptovat" je nekonzistentní a špatně specifikuje akci co má vozík dělat. (akceptovat -> naložit)

*Ve stanici, ve které se vozík aktuálně nachází, může vozík naložit i vyložit jeden či více nákladů.*

Pořadí vyzvednutí materiálů nesouvisí s pořadím vytváření požadavků. 

 - UNSPECIFIED_SUBJECT, Přepsání výrazu "materiál" na "náklad", pro sjednocení s celým textem. (materiál -> náklad)
 - AMB_SUBJECT, "vytvoření" požadavku nemusí znamenat že je požadavek nastaven. (vytvoření -> nastavení)
 - AMB_STATEMENT, Pořadí vyzvednutí může mít více významů. (vyzvednutí v jednotlivých stanicích nebo vyzvednutí nákladu v dané stanici?)
 - AMB_STATEMENT, "nesouvisí" zni hodně abstraktně (nesouvisí -> není dáno)
 - IMPLICIT, Není jasné o jaký požadavek se jedná.

*Pořadí vyzvednutí nákladu v jednotlivých stanicích není dáno pořadím nastavení jednotlivých požadavků pro vyzvednutí nákladu.*

Vozík neakceptuje materiál, pokud jsou všechny jeho sloty obsazené nebo by jeho prevzetím byla překročena maximální nosnost.

 - DANGLING_ELSE, Chybí else.
 - AMB_STATEMENT, "neakceptovat" je nekonzistentní a špatně specifikuje akci co má vozík dělat. (neakceptovat -> nenaloží)
 - UNSPECIFIED_SUBJECT, Přepsání výrazu "materiál" na "náklad", pro sjednocení s celým textem. (materiál -> náklad)
 - UNSPECIFIED_SUBJECT, "převzetím" je nekonzistentí z textem a dá se vyložit více způsoby. (převzetí -> naložení)
 - UNSPECIFIED_SUBJECT, Není jasné k čemu se "nosnost" vztahuje.
 - AMB_SUBJECT, Jaké sloty? (může mít více víznamů)
 - RANDOM_STATEMENT, Věta je přeházená. (THAN, IF -> IF, THAN, ELSE)

*Pokud vozík nemá obsazené všechny jeho nákladové sloty a zároveň nedojde k překročení maximální nosnosti vozíku při naložení dalšího nákladu, tak vozík náklad naloží, jinak vozík náklad nenaloží.*