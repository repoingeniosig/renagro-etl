-- ----------------------------
-- Sequence structure for seq_bosi_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "seq_bosi_id";
CREATE SEQUENCE "seq_bosi_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for seq_tesi_id
-- ----------------------------
DROP SEQUENCE IF EXISTS "seq_tesi_id";
CREATE SEQUENCE "seq_tesi_id" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"seq_bosi_id"', 1, false);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"seq_tesi_id"', 1, false);
