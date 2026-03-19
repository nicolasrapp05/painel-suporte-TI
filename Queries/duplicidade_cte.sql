SET @status_cte = 'Autorizado';
SET @recibo = '4199999999999';

UPDATE conhecimento
SET ctestatus = @status_cte, cterecibo = @recibo, cteprotocolo = @protocolo, ctechave = @chave
WHERE codconhecimento = @cod_cte;

UPDATE cte 
SET ctrl_status = @status_cte, ctrl_autorizacao_protocolo = @protocolo, ctrl_chave = @chave, ctrl_xml = @xml_cte
WHERE ctrl_codcte = @cod_cte;

UPDATE conhecimentoxml
SET XML = @xml_cte, retorno = @xml_cte
WHERE codconhecimento = @cod_cte;
