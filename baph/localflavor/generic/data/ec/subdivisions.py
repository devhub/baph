# encoding: utf8
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _


SUBDIVISIONS = ('PROVINCES', 'CANTONS')

PROVINCES = [
  ('A', _('Azuay')),
  ('B', _('Bolívar')),
  ('F', _('Cañar')),
  ('C', _('Carchi')),
  ('H', _('Chimborazo')),
  ('X', _('Cotopaxi')),
  ('O', _('El Oro')),
  ('E', _('Esmeraldas')),
  ('W', _('Galápagos')),
  ('G', _('Guayaquil')),
  ('I', _('Imbabura')),
  ('L', _('Loja')),
  ('R', _('Los Ríos')),
  ('M', _('Manabí')),
  ('S', _('Morona-Santiago')),
  ('N', _('Napo')),
  ('D', _('Orellana')),
  ('Y', _('Pastaza')),
  ('P', _('Pichincha')),
  ('SE', _('Santa Elena')),
  ('SD', _('Santo Domingo de los Tsáchilas')),
  ('U', _('Sucumbíos')),
  ('T', _('Tungurahua')),
  ('Z', _('Zamora-Chinchipe')),
]

CANTONS = [
  ('1', _('Camilo Ponce Enríquez'), 'A'),
  ('2', _('Chordeleg'), 'A'),
  ('3', _('Cuenca'), 'A'),
  ('4', _('El Pan'), 'A'),
  ('5', _('Girón'), 'A'),
  ('6', _('Guachapala'), 'A'),
  ('7', _('Gualaceo'), 'A'),
  ('8', _('Nabón'), 'A'),
  ('9', _('Oña'), 'A'),
  ('10', _('Paute'), 'A'),
  ('11', _('Pucará'), 'A'),
  ('12', _('San Fernando'), 'A'),
  ('13', _('Santa Isabel'), 'A'),
  ('14', _('Sevilla de Oro'), 'A'),
  ('15', _('Sigsig'), 'A'),
  ('16', _('Caluma'), 'B'),
  ('17', _('Chillanes'), 'B'),
  ('18', _('Chimbo'), 'B'),
  ('19', _('Echeandía'), 'B'),
  ('20', _('Guaranda'), 'B'),
  ('21', _('Las Naves'), 'B'),
  ('22', _('San Miguel'), 'B'),
  ('23', _('Bolívar'), 'C'),
  ('24', _('Espejo'), 'C'),
  ('25', _('Mira'), 'C'),
  ('26', _('Montúfar'), 'C'),
  ('27', _('San Pedro de Huaca'), 'C'),
  ('28', _('Tulcán'), 'C'),
  ('29', _('Azogues'), 'F'),
  ('30', _('Biblián'), 'F'),
  ('31', _('Cañar'), 'F'),
  ('32', _('Déleg'), 'F'),
  ('33', _('El Tambo'), 'F'),
  ('34', _('La Troncal'), 'F'),
  ('35', _('Suscal'), 'F'),
  ('36', _('Alausí'), 'H'),
  ('37', _('Chambo'), 'H'),
  ('38', _('Chunchi'), 'H'),
  ('39', _('Colta'), 'H'),
  ('40', _('Cumandá'), 'H'),
  ('41', _('Guamote'), 'H'),
  ('42', _('Guano'), 'H'),
  ('43', _('Pallatanga'), 'H'),
  ('44', _('Penipe'), 'H'),
  ('45', _('Riobamba'), 'H'),
  ('46', _('La Maná'), 'X'),
  ('47', _('Latacunga'), 'X'),
  ('48', _('Pangua'), 'X'),
  ('49', _('Pujilí'), 'X'),
  ('50', _('Salcedo'), 'X'),
  ('51', _('Saquisilí'), 'X'),
  ('52', _('Sigchos'), 'X'),
  ('53', _('Arenillas'), 'O'),
  ('54', _('Atahualpa'), 'O'),
  ('55', _('Balsas'), 'O'),
  ('56', _('Chilla'), 'O'),
  ('57', _('El Guabo'), 'O'),
  ('58', _('Huaquillas'), 'O'),
  ('59', _('Las Lajas'), 'O'),
  ('60', _('Machala'), 'O'),
  ('61', _('Marcabelí'), 'O'),
  ('62', _('Pasaje'), 'O'),
  ('63', _('Piñas'), 'O'),
  ('64', _('Portovelo'), 'O'),
  ('65', _('Santa Rosa'), 'O'),
  ('66', _('Zaruma'), 'O'),
  ('67', _('Atacames'), 'E'),
  ('68', _('Eloy Alfaro'), 'E'),
  ('69', _('Esmeraldas'), 'E'),
  ('70', _('Muisne'), 'E'),
  ('71', _('Quinindé'), 'E'),
  ('72', _('Río Verde'), 'E'),
  ('73', _('San Lorenzo'), 'E'),
  ('74', _('Isabela'), 'W'),
  ('75', _('San Cristóbal'), 'W'),
  ('76', _('Santa Cruz'), 'W'),
  ('77', _('Alfredo Baquerizo Moreno (Jujan)'), 'G'),
  ('78', _('Balao'), 'G'),
  ('79', _('Balzar (San Jacinto de Balzar)'), 'G'),
  ('80', _('Colimes'), 'G'),
  ('81', _('Coronel Marcelino Maridueña'), 'G'),
  ('82', _('Daule'), 'G'),
  ('83', _('Durán'), 'G'),
  ('84', _('El Empalme'), 'G'),
  ('85', _('El Triunfo'), 'G'),
  ('86', _('General Antonio Elizalde (Bucay)'), 'G'),
  ('87', _('Guayaquil'), 'G'),
  ('88', _('Isidro Ayora'), 'G'),
  ('89', _('La Troncal'), 'G'),
  ('90', _('Lomas de Sargentillo'), 'G'),
  ('91', _('Milagro'), 'G'),
  ('92', _('Naranjal'), 'G'),
  ('93', _('Naranjito'), 'G'),
  ('94', _('Nobol'), 'G'),
  ('95', _('Palestina'), 'G'),
  ('96', _('Pedro Carbo'), 'G'),
  ('97', _('Playas (General Villamil Playas)'), 'G'),
  ('98', _('Salitre'), 'G'),
  ('99', _('Samborondón'), 'G'),
  ('100', _('Santa Lucía'), 'G'),
  ('101', _('Simón Bolívar'), 'G'),
  ('102', _('Yaguachi'), 'G'),
  ('103', _('Antonio Ante'), 'I'),
  ('104', _('Cotacachi'), 'I'),
  ('105', _('Ibarra'), 'I'),
  ('106', _('Otavalo'), 'I'),
  ('107', _('Pimampiro'), 'I'),
  ('108', _('San Miguel de Urcuquí'), 'I'),
  ('109', _('Calvas'), 'L'),
  ('110', _('Catamayo'), 'L'),
  ('111', _('Celica'), 'L'),
  ('112', _('Chaguarpamba'), 'L'),
  ('113', _('Espíndola'), 'L'),
  ('114', _('Gonzanamá'), 'L'),
  ('115', _('Loja'), 'L'),
  ('116', _('Macará'), 'L'),
  ('117', _('Olmedo'), 'L'),
  ('118', _('Paltas'), 'L'),
  ('119', _('Pindal'), 'L'),
  ('120', _('Puyango'), 'L'),
  ('121', _('Quilanga'), 'L'),
  ('122', _('Saraguro'), 'L'),
  ('123', _('Sozoranga'), 'L'),
  ('124', _('Zapotillo'), 'L'),
  ('125', _('Baba'), 'R'),
  ('126', _('Babahoyo'), 'R'),
  ('127', _('Buena Fé'), 'R'),
  ('128', _('Mocache'), 'R'),
  ('129', _('Montalvo'), 'R'),
  ('130', _('Palenque'), 'R'),
  ('131', _('Pueblo Viejo'), 'R'),
  ('132', _('Quevedo'), 'R'),
  ('133', _('Quinsaloma'), 'R'),
  ('134', _('Urdaneta'), 'R'),
  ('135', _('Valencia'), 'R'),
  ('136', _('Ventanas'), 'R'),
  ('137', _('Vinces'), 'R'),
  ('138', _('Bolívar'), 'M'),
  ('139', _('Chone'), 'M'),
  ('140', _('El Carmen'), 'M'),
  ('141', _('Flavio Alfaro'), 'M'),
  ('142', _('Jama'), 'M'),
  ('143', _('Jaramijó'), 'M'),
  ('144', _('Jipijapa'), 'M'),
  ('145', _('Junín'), 'M'),
  ('146', _('Manta'), 'M'),
  ('147', _('Montecristi'), 'M'),
  ('148', _('Olmedo'), 'M'),
  ('149', _('Paján'), 'M'),
  ('150', _('Pedernales'), 'M'),
  ('151', _('Pichincha'), 'M'),
  ('152', _('Portoviejo'), 'M'),
  ('153', _('Puerto López'), 'M'),
  ('154', _('Rocafuerte'), 'M'),
  ('155', _('San Vicente'), 'M'),
  ('156', _('Santa Ana'), 'M'),
  ('157', _('Sucre'), 'M'),
  ('158', _('Tosagua'), 'M'),
  ('159', _('Veinticuatro de Mayo'), 'M'),
  ('160', _('Gualaquiza'), 'S'),
  ('161', _('Huamboya'), 'S'),
  ('162', _('Limón Indanza'), 'S'),
  ('163', _('Logroño'), 'S'),
  ('164', _('Morona'), 'S'),
  ('165', _('Pablo Sexto'), 'S'),
  ('166', _('Palora'), 'S'),
  ('167', _('San Juan Bosco'), 'S'),
  ('168', _('Santiago de Méndez'), 'S'),
  ('169', _('Sucúa'), 'S'),
  ('170', _('Taisha'), 'S'),
  ('171', _('Tiwintza'), 'S'),
  ('172', _('Archidona'), 'N'),
  ('173', _('Carlos Julio Arosemena Tola'), 'N'),
  ('174', _('El Chaco'), 'N'),
  ('175', _('Quijos'), 'N'),
  ('176', _('Tena'), 'N'),
  ('177', _('Aguarico'), 'D'),
  ('178', _('Francisco de Orellana'), 'D'),
  ('179', _('Joya de los Sachas'), 'D'),
  ('180', _('Loreto'), 'D'),
  ('181', _('Arajuno'), 'Y'),
  ('182', _('Mera'), 'Y'),
  ('183', _('Pastaza'), 'Y'),
  ('184', _('Santa Clara'), 'Y'),
  ('185', _('Cayambe'), 'P'),
  ('186', _('Mejía'), 'P'),
  ('187', _('Pedro Moncayo'), 'P'),
  ('188', _('Pedro Vicente Maldonado'), 'P'),
  ('189', _('Puerto Quito'), 'P'),
  ('190', _('Quito'), 'P'),
  ('191', _('Rumiñahui'), 'P'),
  ('192', _('San Miguel de Los Bancos'), 'P'),
  ('193', _('La Libertad'), 'SE'),
  ('194', _('Salinas'), 'SE'),
  ('195', _('Santa Elena'), 'SE'),
  ('196', _('La Concordia'), 'SD'),
  ('197', _('Santo Domingo de los Colorados'), 'SD'),
  ('198', _('Cascales'), 'U'),
  ('199', _('Cuyabeno'), 'U'),
  ('200', _('Gonzalo Pizarro'), 'U'),
  ('201', _('Lago Agrio'), 'U'),
  ('202', _('Putumayo'), 'U'),
  ('203', _('Shushufindi'), 'U'),
  ('204', _('Sucumbíos'), 'U'),
  ('205', _('Ambato'), 'T'),
  ('206', _('Baños'), 'T'),
  ('207', _('Cevallos'), 'T'),
  ('208', _('Mocha'), 'T'),
  ('209', _('Patate'), 'T'),
  ('210', _('Pelileo'), 'T'),
  ('211', _('Píllaro'), 'T'),
  ('212', _('Quero'), 'T'),
  ('213', _('Tisaleo'), 'T'),
  ('214', _('Centinela del Cóndor'), 'Z'),
  ('215', _('Chinchipe'), 'Z'),
  ('216', _('El Pangui'), 'Z'),
  ('217', _('Nangaritza'), 'Z'),
  ('218', _('Palanda'), 'Z'),
  ('219', _('Paquisha'), 'Z'),
  ('220', _('Yacuambi'), 'Z'),
  ('221', _('Yantzaza'), 'Z'),
  ('222', _('Zamora'), 'Z'),
]
