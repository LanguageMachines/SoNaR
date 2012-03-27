<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet version="1.0" xmlns="http://www.w3.org/1999/xhtml" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:imdi="http://www.mpi.nl/IMDI/Schema/IMDI" xmlns:folia="http://ilk.uvt.nl/folia">

<xsl:output method="html" encoding="UTF-8" omit-xml-declaration="yes" doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" indent="yes" cdata-section-elements="script"/>


<xsl:template match="/folia:FoLiA">
    <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
            <script type="text/javascript" src="http://code.jquery.com/jquery-1.5.1.min.js"></script>
            <xsl:choose>
             <xsl:when test="/FoLiA/metadata/imdi:METATRANSCRIPT/imdi:Session/imdi:Title">
                <title>SoNaR - <xsl:value-of select="/FoLiA/metadata/imdi:METATRANSCRIPT/imdi:Session/imdi:Title"/></title>
             </xsl:when>
             <xsl:otherwise>
                <title>SoNaR - <xsl:value-of select="@xml:id"/></title>
             </xsl:otherwise>
            </xsl:choose>
			<style type="text/css">
				body {
					/*background: #222222;*/
					background: #b7c8c7;
					font-family: sans-serif;
					font-size: 10pt;
					margin-bottom:120px;
				}

				div.text {
					width: 700px;
					margin-top: 50px;
					margin-left: auto;
					margin-right: auto;
					padding: 10px;    
					padding-left: 50px;
					padding-right: 50px;
					text-align: left;
					background: white;
					border: 2px solid black;
				}

				div.div {
					padding-left: 0px;
					padding-top: 10px;
					padding-bottom: 10px;    
				}

				#metadata {
					font-family: sans-serif;
					width: 700px;
					font-size: 90%;
					margin-left: auto;
					margin-right: auto;
					margin-top: 5px;
					margin-bottom: 5px;
					background: #b4d4d1; /*#FCFFD0;*/
					border: 1px solid #628f8b;
					width: 40%;
					padding: 5px;
				}
				#metadata table {
					text-align: left;
				}

				#text {
					border: 1px solid #628f8b;
					width: 60%; 
					max-width: 1024px;
					background: white;
					padding: 20px;
					padding-right: 100px; 
					margin-top: 5px;
					margin-left: auto; 
					margin-right: auto; 
					color: #222;
				}
				.sentence {
					display: inline;
				}
				.word { 
					display: inline; 
					color: black; 
					position: relative; 
					text-decoration: none; 
					z-index: 24; 
				}
				#text {
					border: 1px solid #628f8b;
					width: 60%; 
					max-width: 1024px;
					background: white;
					padding: 20px;
					padding-right: 100px; 
					margin-top: 5px;
					margin-left: auto; 
					margin-right: auto; 
					color: #222;
				}
				.sentence {
					display: inline;
				}
				.word { 
					display: inline; 
					color: black; 
					position: relative; 
					text-decoration: none; 
					z-index: 24; 
				}
				
				.wordtext {
					display: inline;
					text-decoration: none;
				}

				.word>.attributes { display: none; font-size: 12pt; font-weight: normal; }
				.word:hover>.wordtext { 
					text-decoration: underline; 
					z-index: 20;
				}
				
				.word:hover>.attributes { 
					display: block; 
					position: absolute;
					width: 320px; 
					font-size: 12pt;
					left: 2em; 
					top: 2em;
					background: #b4d4d1; /*#FCFFD0;*/
					opacity: 0.9; filter: alpha(opacity = 90); 
					border: 1px solid #628f8b; 
					padding: 5px; 
					text-decoration: none;
					z-index: 26; 
				}
				.attributes dt {
					color: #254643;
					font-weight: bold;
				}
				.attributes dd {
					color: black;
					font-family: monospace;
				}
				.attributes .wordid {
					display: inline-block:
					width: 100%;
					font-size: 75%;
					color: #555;
					font-family: monospace;
					text-align: center;
				}
				.event {
					padding: 10px;
					border: 1px solid #4f7d87;
				}
           	
            </style>            
        </head>
        <body>
            <xsl:apply-templates select="folia:text" />
        </body>
    </html>
</xsl:template>


<xsl:template match="folia:text">
 <div class="text">
   <xsl:choose>
   <xsl:when test="/folia:div">
    <xsl:apply-templates select="/folia:div" />
   </xsl:when>
   <xsl:when test="/folia:event">
     <xsl:apply-templates select="/folia:event" />
   </xsl:when>
   <xsl:when test="//folia:p">
    <xsl:apply-templates select="//folia:p|//folia:head" />
   </xsl:when>
   <xsl:when test="//folia:s">
    <xsl:apply-templates select="//folia:s|//folia:head" />
   </xsl:when> 
   <xsl:otherwise>
    <span class="error">No content found in this text!</span>
   </xsl:otherwise>
  </xsl:choose>
 </div>
</xsl:template>

<xsl:template match="folia:div">
 <div class="div">
  <xsl:apply-templates />
 </div>
</xsl:template>

<xsl:template match="folia:div">
 <div class="event">
  <xsl:apply-templates />
 </div>
</xsl:template>


<xsl:template match="folia:p">
 <p>
  <xsl:apply-templates />
 </p>
</xsl:template>


<xsl:template match="folia:head">
 <h1>
  <xsl:apply-templates />
 </h1>
</xsl:template>

<xsl:template match="folia:s">
 <span class="s">
  <xsl:apply-templates />
 </span>
</xsl:template>

<xsl:template match="folia:w">
 <span id="{@xml:id}" class="word">
        <span class="attributes">
                <span class="wordid"><xsl:value-of select="@xml:id" /></span>
                <dl>
                        <xsl:apply-templates />
                </dl>
        </span>
        <span class="wordtext"><xsl:value-of select="folia:t"/></span>
 </span>
 <xsl:text> </xsl:text> <!-- TODO: implement @nospace check -->
</xsl:template>

<xsl:template match="folia:pos">
 <dt>PoS</dt><dd><xsl:value-of select="@class"/></dd>
</xsl:template>

<xsl:template match="folia:lemma">
 <dt>Lemma</dt><dd><xsl:value-of select="@class"/></dd>
</xsl:template>

</xsl:stylesheet>