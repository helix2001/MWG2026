<HTML>

<HEAD>
<TITLE>Javascript Great Circle Calculator</TITLE>
<META name="description"
content="Javascript Great Circle Calculator using ellipsoidal earth models">
<META name="keywords"
content="FAI,great circle, ellipsoid, geodesic, course, navigation">

<SCRIPT LANGUAGE="JAVASCRIPT">

<!-- hide this script tag's contents from old browsers
// Copyright 1997 Ed Williams. All rights reserved

decpl=4  // Dec places of minutes output
//**************CD****************
function ClearFormCD(){

    document.InputFormCD.lat1.value = "0:00.00";
    document.InputFormCD.lat2.value = "0:00.00";
    document.InputFormCD.lon1.value = "0:00.00";
    document.InputFormCD.lon2.value = "0:00.00";
    document.OutputFormCD.crs12.value = "";
    document.OutputFormCD.crs21.value = "";
    document.OutputFormCD.d12.value = "";


}

function ComputeFormCD(){
    //get select  values
var signlat1,signlat2,signlon1,signlon2,dc
var lat1,lat2,lon1,lon2
var d,crs12,crs21
var argacos
var a,invf
  /* Input and validate data */
signlat1=signlatlon(document.InputFormCD.NS1)
signlat2=signlatlon(document.InputFormCD.NS2)
signlon1=signlatlon(document.InputFormCD.EW1)
signlon2=signlatlon(document.InputFormCD.EW2)


lat1=(Math.PI/180)*signlat1*checkField(document.InputFormCD.lat1)
lat2=(Math.PI/180)*signlat2*checkField(document.InputFormCD.lat2)
lon1=(Math.PI/180)*signlon1*checkField(document.InputFormCD.lon1)
lon2=(Math.PI/180)*signlon2*checkField(document.InputFormCD.lon2)

//alert("lat1=" + lat1 + "lon1=" + lon1 +"\nlat2=" +lat2+ "lon2="+lon2)

dc=dconv(document.OutputFormCD.Dunit) /* get distance conversion factor */
//alert("dc=" +dc)

ellipse=getEllipsoid(document.OutputFormCD.Model) //get ellipse
//showProps(ellipse,"ellipse")

if (ellipse.name=="Sphere"){
  // spherical code
  cd=crsdist(lat1,lon1,lat2,lon2) // compute crs and distance 
  crs12 =cd.crs12*(180/Math.PI)
  crs21 =cd.crs21*(180/Math.PI)
  d=cd.d*(180/Math.PI)*60*dc  // go to physical units  
  } else {
  // elliptic code
  cde=crsdist_ell(lat1,-lon1,lat2,-lon2,ellipse)  // ellipse uses East negative
  crs12 =cde.crs12*(180/Math.PI)  
  crs21 =cde.crs21*(180/Math.PI)
  d=cde.d*dc  // go to physical units
  }

//alert("d="+d+"  crs12="+crs12+"   crs21="+crs21)
document.OutputFormCD.crs12.value=crs12
document.OutputFormCD.crs21.value=crs21
document.OutputFormCD.d12.value=d
}

function crsdist(lat1,lon1,lat2,lon2){ // radian args
/* compute course and distance (spherical) */

if ((lat1+lat2==0.) && (Math.abs(lon1-lon2)==Math.PI)
                    && (Math.abs(lat1) != (Math.PI/180)*90.)){
    alert("Course between antipodal points is undefined")
    }

with (Math){

  d=acos(sin(lat1)*sin(lat2)+cos(lat1)*cos(lat2)*cos(lon1-lon2))

  if ((d==0.) || (lat1==-(PI/180)*90.)){
     crs12=2*PI
  } else if (lat1==(PI/180)*90.){
     crs12=PI
  } else {
     argacos=(sin(lat2)-sin(lat1)*cos(d))/(sin(d)*cos(lat1))
     if (sin(lon2-lon1) < 0){       
       crs12=acosf(argacos)    
     }
     else{
       crs12=2*PI-acosf(argacos)    
     }
  }
  if ((d==0.) || (lat2==-(PI/180)*90.)){
     crs21=0.
  } else if (lat2==(PI/180)*90.){
     crs21=PI
  }else{
     argacos=(sin(lat1)-sin(lat2)*cos(d))/(sin(d)*cos(lat2))
     if (sin(lon1-lon2)<0){       
       crs21=acosf(argacos)    
     }
     else{
       crs21=2*PI-acosf(argacos)    
     }
  }
}
out=new MakeArray(0)
out.d=d
out.crs12=crs12
out.crs21=crs21
return out
}

function crsdist_ell(glat1,glon1,glat2,glon2,ellipse){
// glat1 initial geodetic latitude in radians N positive 
// glon1 initial geodetic longitude in radians E positive 
// glat2 final geodetic latitude in radians N positive 
// glon2 final geodetic longitude in radians E positive 
a=ellipse.a
f=1/ellipse.invf
//alert("a="+a+" f="+f)
var r, tu1, tu2, cu1, su1, cu2, s1, b1, f1
var x, sx, cx, sy, cy,y, sa, c2a, cz, e, c, d
var EPS= 0.00000000005
var faz, baz, s
var iter=1
var MAXITER=100
  if ((glat1+glat2==0.) && (Math.abs(glon1-glon2)==Math.PI)){
    alert("Course and distance between antipodal points is undefined")
    glat1=glat1+0.00001 // allow algorithm to complete
    }
  if (glat1==glat2 && (glon1==glon2 || Math.abs(Math.abs(glon1-glon2)-2*Math.PI) <  EPS)){
    alert("Points 1 and 2 are identical- course undefined")
    out=new MakeArray(0)
    out.d=0
    out.crs12=0
    out.crs21=Math.PI
    return out
  }
  r = 1 - f
  tu1 = r * Math.tan (glat1)
  tu2 = r * Math.tan (glat2)
  cu1 = 1. / Math.sqrt (1. + tu1 * tu1)
  su1 = cu1 * tu1
  cu2 = 1. / Math.sqrt (1. + tu2 * tu2)
  s1 = cu1 * cu2
  b1 = s1 * tu2
  f1 = b1 * tu1
  x = glon2 - glon1
  d = x + 1 // force one pass
  while ((Math.abs(d - x) > EPS) && (iter < MAXITER))
    {
      iter=iter+1
      sx = Math.sin (x)
//       alert("sx="+sx)
      cx = Math.cos (x)
      tu1 = cu2 * sx
      tu2 = b1 - su1 * cu2 * cx
      sy = Math.sqrt(tu1 * tu1 + tu2 * tu2)
      cy = s1 * cx + f1
      y = atan2 (sy, cy)
      sa = s1 * sx / sy
      c2a = 1 - sa * sa
      cz = f1 + f1
      if (c2a > 0.)
	cz = cy - cz / c2a
      e = cz * cz * 2. - 1.
      c = ((-3. * c2a + 4.) * f + 4.) * c2a * f / 16.
      d = x
      x = ((e * cy * c + cz) * sy * c + y) * sa
      x = (1. - c) * x * f + glon2 - glon1
    }
  faz = modcrs(atan2(tu1, tu2))
  baz = modcrs(atan2(cu1 * sx, b1 * cx - su1 * cu2) + Math.PI)
  x = Math.sqrt ((1 / (r * r) - 1) * c2a + 1)
  x +=1
  x = (x - 2.) / x
  c = 1. - x
  c = (x * x / 4. + 1.) / c
  d = (0.375 * x * x - 1.) * x
  x = e * cy
  s = ((((sy*sy*4.-3.)*(1.-e-e)*cz*d/6.-x)*d/4.+cz)*sy*d+y)*c*a*r
  out=new MakeArray(0)
  out.d=s
  out.crs12=faz
  out.crs21=baz
  if (Math.abs(iter-MAXITER)<EPS){
    alert("Algorithm did not converge")
  }
  return out

}
//**************Dir*************
function ClearFormDir(){

    document.InputFormDir.lat1.value = "0:00.00";
    document.InputFormDir.crs12.value = "360";
    document.InputFormDir.lon1.value = "0:00.00";
    document.InputFormDir.d12.value = "0.0";
    document.OutputFormDir.lat2.value = "";
    document.OutputFormDir.lat2ns.value = "N";
    document.OutputFormDir.lon2.value = "";
    document.OutputFormDir.lon2ew.value = "E";
}


function ComputeFormDir(){
    //get select  values
var signlat1,signlon1,dc
var lat1,lon1
var d12,crs12
var a,invf
  /* Input and validate data */
signlat1=signlatlon(document.InputFormDir.NS1)
signlon1=signlatlon(document.InputFormDir.EW1)
lat1=(Math.PI/180)*signlat1*checkField(document.InputFormDir.lat1)
lon1=(Math.PI/180)*signlon1*checkField(document.InputFormDir.lon1)

d12=document.InputFormDir.d12.value
dc=dconv(document.OutputFormDir.Dunit) /* get distance conversion factor */
d12 /=dc  // in nm
//alert("dc=" +dc)

crs12=document.InputFormDir.crs12.value*Math.PI/180.  // radians
//alert("lat1="+lat1+" lon1="+lon1+" d12="+d12+" crs12="+crs12)

ellipse=getEllipsoid(document.OutputFormDir.Model) //get ellipse
//showProps(ellipse,"ellipse")

if (ellipse.name=="Sphere"){
  // spherical code
  d12 /=(180*60/Math.PI)  // in radians
  cd=direct(lat1,lon1,crs12,d12) 
  lat2 =cd.lat*(180/Math.PI)
  lon2 =cd.lon*(180/Math.PI)
  } else {
  // elliptic code
  cde=direct_ell(lat1,-lon1,crs12,d12,ellipse)  // ellipse uses East negative
  lat2 =cde.lat*(180/Math.PI)  
  lon2 =-cde.lon*(180/Math.PI)                  // ellipse uses East negative
  }

//alert("d="+d+"  crs12="+crs12+"   crs21="+crs21)


if (lat2 >=0) {
   document.OutputFormDir.lat2ns.value="N"
   } else {
   document.OutputFormDir.lat2ns.value="S"
   }
if (lon2 > 0) {
   document.OutputFormDir.lon2ew.value="W"
   } else {
   document.OutputFormDir.lon2ew.value="E"
   }

lat2s=degtodm(Math.abs(lat2),decpl)
document.OutputFormDir.lat2.value=lat2s
lon2s=degtodm(Math.abs(lon2),decpl)
document.OutputFormDir.lon2.value=lon2s
}


function direct(lat1,lon1,crs12,d12) {
  var EPS= 0.00000000005
  var dlon,lat,lon
// 5/16 changed to "long-range" algorithm
  if ((Math.abs(Math.cos(lat1))<EPS) && !(Math.abs(Math.sin(crs12))<EPS)){
    alert("Only N-S courses are meaningful, starting at a pole!")
  }

  lat=Math.asin(Math.sin(lat1)*Math.cos(d12)+
                Math.cos(lat1)*Math.sin(d12)*Math.cos(crs12))
  if (Math.abs(Math.cos(lat))<EPS){
    lon=0.; //endpoint a pole
  }else{
    dlon=Math.atan2(Math.sin(crs12)*Math.sin(d12)*Math.cos(lat1),
                  Math.cos(d12)-Math.sin(lat1)*Math.sin(lat))
    lon=mod( lon1-dlon+Math.PI,2*Math.PI )-Math.PI
  }
//  alert("lat1="+lat1+" lon1="+lon1+" crs12="+crs12+" d12="+d12+" lat="+lat+" lon="+lon)
  out=new MakeArray(0)
  out.lat=lat
  out.lon=lon
  return out
}

function direct_ell(glat1,glon1,faz,s,ellipse) {
// glat1 initial geodetic latitude in radians N positive 
// glon1 initial geodetic longitude in radians E positive 
// faz forward azimuth in radians
// s distance in units of a (=nm)

var EPS= 0.00000000005
var r, tu, sf, cf, b, cu, su, sa, c2a, x, c, d, y, sy, cy, cz, e
var glat2,glon2,baz,f

  if ((Math.abs(Math.cos(glat1))<EPS) && !(Math.abs(Math.sin(faz))<EPS)){
    alert("Only N-S courses are meaningful, starting at a pole!")
  }

  a=ellipse.a
  f=1/ellipse.invf
  r = 1 - f
  tu = r * Math.tan (glat1)
  sf = Math.sin (faz)
  cf = Math.cos (faz)
  if (cf==0){
     b=0.
  }else{
     b=2. * atan2 (tu, cf)
  }
  cu = 1. / Math.sqrt (1 + tu * tu)
  su = tu * cu
  sa = cu * sf
  c2a = 1 - sa * sa
  x = 1. + Math.sqrt (1. + c2a * (1. / (r * r) - 1.))
  x = (x - 2.) / x
  c = 1. - x
  c = (x * x / 4. + 1.) / c
  d = (0.375 * x * x - 1.) * x
  tu = s / (r * a * c)
  y = tu
  c = y + 1
  while (Math.abs (y - c) > EPS)
    {
      sy = Math.sin (y)
      cy = Math.cos (y)
      cz = Math.cos (b + y)
      e = 2. * cz * cz - 1.
      c = y
      x = e * cy
      y = e + e - 1.
      y = (((sy * sy * 4. - 3.) * y * cz * d / 6. + x) *
              d / 4. - cz) * sy * d + tu
    }

  b = cu * cy * cf - su * sy
  c = r * Math.sqrt (sa * sa + b * b)
  d = su * cy + cu * sy * cf
  glat2 = modlat(atan2 (d, c))
  c = cu * cy - su * sy * cf
  x = atan2 (sy * sf, c)
  c = ((-3. * c2a + 4.) * f + 4.) * c2a * f / 16.
  d = ((e * cy * c + cz) * sy * c + y) * sa
  glon2 = modlon(glon1 + x - (1. - c) * d * f)	// fix date line problems 
  baz = modcrs(atan2 (sa, b) + Math.PI)

  out=new MakeArray(0)
  out.lat=glat2
  out.lon=glon2
  out.crs21=baz
  return out
}



//***************Utility***************
function Link(){
type=new MakeArray(3)
type[1]="airport-info"
type[2]="navaid-info"
type[3]="fix-info"
var query=type[document.spheroid.Fixtype.selectedIndex+1]
var ref="http://www.airnav.com/cgi-bin/"+query+"?"+
 document.spheroid.Fix.value
var  newWindow=window.open(ref,"")
     newWindow=window.open(ref,"")  //twice because of Netscape bug
}

function signlatlon(selection){
var sign
if (selection.selectedIndex==0){
   sign=1
}else{
   sign=-1
}
return sign
}

function MakeArray(n){
   this.length=n
   for (var i=1;i<=n;i++){
     this[i]=0
   }
   return this
}

function dconv(selection){
   dc=new MakeArray(3)
   dc[1]=1.
   dc[2]=1.852 //km
   dc[3]=185200.0/160934.40 // 1.150779448 sm
   dc[4]=185200.0/30.48 // 6076.11549  //ft
   return dc[selection.selectedIndex+1]
}

function ellipsoid(name, a, invf){
  /* constructor */
  this.name=name
  this.a=a
  this.invf=invf
}

function getEllipsoid(selection){
  no_selections=10
  ells= new MakeArray(no_selections)
  ells[1]= new ellipsoid("Sphere", 180*60/Math.PI,"Infinite") // first one
  ells[2]= new ellipsoid("WGS84",6378.137/1.852,298.257223563)
  ells[3]= new ellipsoid("NAD27",6378.2064/1.852,294.9786982138)
  ells[4]= new ellipsoid("International",6378.388/1.852,297.0)
  ells[5]= new ellipsoid("Krasovsky",6378.245/1.852,298.3)
  ells[6]= new ellipsoid("Bessel",6377.397155/1.852,299.1528)
  ells[7]= new ellipsoid("WGS72",6378.135/1.852,298.26)
  ells[8]= new ellipsoid("WGS66",6378.145/1.852,298.25)
  ells[9]= new ellipsoid("FAI sphere",6371.0/1.852,1000000000.)
  ells[10]= new ellipsoid("User",0.,0.)  // last one!

  if (selection.selectedIndex+1==no_selections){ // user defined
    ells[no_selections].name="User"
    ells[no_selections].a= document.spheroid.major_radius.value/1.852
    ells[no_selections].invf=document.spheroid.inverse_f.value
    if (ells[no_selections].invf=="Infinite"){
       ells[no_selections].invf=1000000000.
    }
  } else {
//  document.spheroid.major_radius.value=ells[selection.selectedIndex+1].a*1.852
//  document.spheroid.inverse_f.value=ells[selection.selectedIndex+1].invf
  }
  return ells[selection.selectedIndex+1]
}

function parselatlon(instr){
// Parse strings dd.dd dd:mm.mm dd:mm:ss.ss
var deg,min,sec,colonIndex,degstr,minstr,str
str=instr
colonIndex=str.indexOf(":")
if (colonIndex==-1){ // dd.dd?
   if (!isPosNumber(str)){
      badLLFormat(instr)
   return 0.
   } else {
   return parseFloat(str)
   }
} // falls through if we have a colon 

degstr=str.substring(0,colonIndex)  //DD
str=str.substring(colonIndex+1,str.length) //MM...
if (!isPosInteger(degstr)){
   badLLFormat(instr)
   return 0.
} else {
   deg=parseFloat(degstr+".0")
}
//now repeat to pick off minutes
colonIndex=str.indexOf(":")
if (colonIndex==-1){ // dd:mm.mm?
   if (!isPosNumber(str)){
      badLLFormat(instr)
      return 0.
   } else {
   min=parseFloat(str)
   if (min < 60.){
     return deg+parseFloat(str)/60.
   } else {
   badLLFormat(instr)
      return 0.
   }  
   
   }
}// falls through if we have a second colon

minstr=str.substring(0,colonIndex)+".0"  //MM.0
str=str.substring(colonIndex+1,str.length) //SS.SS
if (!isPosNumber(minstr) || !isPosNumber(str)){
  badLLFormat(instr)
  return 0.
} else {
  if ( (parseFloat(minstr) < 60) && (parseFloat(str) < 60.)){
    return deg+ parseFloat(minstr)/60.+parseFloat(str)/3600.
  } else {
    badLLFormat(instr)
    return 0.
  }      
}
}


function badLLFormat(str){
alert(str+ " is an invalid lat/lon format\n"+
            "Use DD.DD DD:MM.MM or DD:MM:SS.SS")
}

function isPosInteger(instr){ //integer only
str=""+instr // force to string type
for (var i=0;i<str.length;i++) {
  var oneChar=str.charAt(i)
  if (oneChar < "0" || oneChar > "9") {
    return false
  }
}
return true
}

function isPosNumber(instr){ //integer or float
str=""+instr // force to string type
oneDecimal=false
for (var i=0;i<str.length;i++) {
  var oneChar=str.charAt(i)
  if (oneChar=="." && !oneDecimal){
     oneDecimal=true
     continue
  }
  if (oneChar < "0" || oneChar > "9") {
    return false
  }
}
return true
}

function checkField(field){
var str=field.name
var latlon
latlon=parselatlon(field.value)
if (str.substring(0,3)=="lat") {
   if (latlon > 90.) {
      alert ("Latitudes cannot exceed 90 degrees")
      field.focus()  // Doesn't work!
      field.select()
   }
}
if (str.substring(0,3)=="lon") {
   if (latlon > 180.) {
      alert ("Longitudes cannot exceed 180 degrees")
      field.focus()
      field.select()      
   }
}
return latlon
}

function acosf(x){ /* protect against rounding error on input argument */
if (Math.abs(x) >1){
    x /=Math.abs(x)
  }
return Math.acos(x)
}

function atan2(y,x){
var out
  if (x <0)            { out= Math.atan(y/x)+Math.PI}
  if ((x >0) && (y>=0)){ out= Math.atan(y/x)}
  if ((x >0) && (y<0)) { out= Math.atan(y/x)+2*Math.PI}
  if ((x==0) && (y>0)) { out= Math.PI/2}
  if ((x==0) && (y<0)) { out= 3*Math.PI/2}  
  if ((x==0) && (y==0)) {
    alert("atan2(0,0) undefined")
    out= 0.
  }  
  return out
}

function mod(x,y){
  return x-y*Math.floor(x/y)
}

function modlon(x){
  return mod(x+Math.PI,2*Math.PI)-Math.PI
}

function modcrs(x){
  return mod(x,2*Math.PI)
}

function modlat(x){
  return mod(x+Math.PI/2,2*Math.PI)-Math.PI/2
}

function degtodm(deg,decplaces){
// returns a rounded string DD:MM.MMMM
var deg1=Math.floor(deg)
var min=60.*(deg-Math.floor(deg))
var mins=format(min,decplaces)
//alert("deg1="+deg1+" mins="+mins)
// rounding may have rounded mins to 60.00-- sigh
if (mins.substring(0,1)=="6" && mins >59.0){
  deg1 +=1
  mins=format(0,decplaces)
}
return deg1+":"+mins
}

function format(expr, decplaces){
var str= "" +Math.round(eval(expr)*Math.pow(10,decplaces))
while (str.length <=decplaces) {
  str= "0" + str
}
var decpoint=str.length-decplaces
return str.substring(0,decpoint)+"."+str.substring(decpoint,str.length)
}


function showProps(obj,objName){
var result=""
for (var i in obj){
result +=objName + "." + i + " = " + obj[i] + "\n"
}
alert(result)
}

// -- done hiding from old browsers -->

</SCRIPT>
</HEAD>

<BODY>
<CENTER>
<H1>Great Circle Calculator.</H1>
</CENTER>

<CENTER><H3>By Ed Williams</H3></CENTER>
<P> You need Javascript enabled if you want this page to do anything useful!
For Netscape, it's under Options/Network Preferences/Languages.
</P>
<H3> <A NAME="CrsDist">Compute true course and distance between points.</A> </H3>

<P> Enter lat/lon of points, select distance units and earth model and click
"compute". Lat/lons may be entered in DD.DD, DD:MM.MM or
DD:MM:SS.SS formats.</P>
<p> Note that if either point is very close to a pole,
the course may be inaccurate, because of its extreme sensitivity to position
and inevitable rounding error. </P>

<CENTER>
<FORM NAME="InputFormCD" method=POST>
<TABLE border=1>
<TR>
<TD COLSPAN=2><DIV ALIGN=CENTER>Lat1</DIV></TD>

<TD COLSPAN=2><DIV ALIGN=CENTER>Lon1</DIV></TD>
<CAPTION> Input Data
</TR>
<TR>
<TD><INPUT TYPE=TEXT NAME=lat1  SIZE=10 value="0:00.00"  ></TD>
<TD><SELECT Name="NS1">
   <OPTION SELECTED>N<OPTION>S</SELECT></TD>
<TD><INPUT TYPE=TEXT NAME=lon1 SIZE=10 value="0:00.00"></TD>
<TD><SELECT Name="EW1">
   <OPTION SELECTED>W<OPTION>E</SELECT></TD>
</TR>
<TR>
<TD COLSPAN=2><DIV ALIGN=CENTER>Lat2</DIV></TD>

<TD COLSPAN=2><DIV ALIGN=CENTER>Lon2</DIV></TD>

</TR>
<TR>
<TD><INPUT TYPE=TEXT NAME=lat2 SIZE=10 value="0:00.00"  ></TD>
<TD><SELECT Name="NS2">
   <OPTION SELECTED>N<OPTION>S</SELECT></TD>
<TD><INPUT TYPE=TEXT NAME=lon2 SIZE=10 value="0:00.00"></TD>
<TD><SELECT Name="EW2">
   <OPTION SELECTED>W<OPTION>E</SELECT></TD>
</TR>
</TABLE>
</FORM>
<P></P>
<P></P>


<FORM NAME="OutputFormCD" method=POST>
<TABLE border=1>
<TR>
<TD><DIV ALIGN=CENTER>Course 1-2</DIV></TD>
<TD><DIV ALIGN=CENTER>Course 2-1</DIV></TD>
<TD><DIV ALIGN=CENTER>Distance</DIV></TD>
</TR>
<TR>
<TD><INPUT TYPE=TEXT NAME=crs12  SIZE=8 ></TD>
<TD><INPUT TYPE=TEXT NAME=crs21  SIZE=8 ></TD>
<TD><INPUT TYPE=TEXT NAME=d12    SIZE=9 ></TD>
</TR>
<CAPTION> Output
</TABLE>
</CENTER>
<P></P>

<P> Distance Units: 
<SELECT Name="Dunit">
   <OPTION SELECTED>nm<OPTION>km<OPTION>sm<OPTION>ft</SELECT>
    Earth model:
<SELECT Name="Model">
   <OPTION>Spherical (1'=1nm)
   <OPTION SELECTED>WGS84/NAD83/GRS80
   <OPTION>Clarke (1866)/NAD27
   <OPTION>International
   <OPTION>Krasovsky
   <OPTION>Bessel (1841)
   <OPTION>WGS72
   <OPTION>WGS66
   <OPTION>FAI sphere
   <OPTION>User defined
</SELECT>
</P>
<P>
<INPUT TYPE="button" VALUE="Compute" onClick="ComputeFormCD()">
<INPUT TYPE="button"  VALUE="Reset" onClick="ClearFormCD()">

</P>
</FORM>
<HR>


<H3> <A NAME="CrsDist">Compute lat/lon given radial and
distance from a known point</A> </H3>

<P> Enter lat/lon of initial point, true course and distance.
Select distance units and earth model and click
"compute". Lat/lons may be entered in DD.DD, DD:MM.MM or
DD:MM:SS.SS formats.</P>
<p> Note that the starting point cannot be a pole. </p>


<CENTER>
<FORM NAME="InputFormDir" method=POST>
<TABLE border=1>
<TR>
<TD COLSPAN=2><DIV ALIGN=CENTER>Lat1</DIV></TD>

<TD COLSPAN=2><DIV ALIGN=CENTER>Lon1</DIV></TD>

</TR>
<TR>
<TD><INPUT TYPE=TEXT NAME=lat1  SIZE=10 value="0:00.00"></TD>
<TD><SELECT Name="NS1">
   <OPTION SELECTED>N<OPTION>S</SELECT></TD>
<TD><INPUT TYPE=TEXT NAME=lon1 SIZE=10 value="0:00.00" ></TD>
<TD><SELECT Name="EW1">
   <OPTION SELECTED>W<OPTION>E</SELECT></TD>
<TD></TD>
</TR>
<TR>
<TD><DIV ALIGN=CENTER>Course 1-2</DIV></TD>
<TD></TD>
<TD><DIV ALIGN=CENTER>Distance 1-2</DIV></TD>
</TR>

<TR>
<TD><INPUT TYPE=TEXT NAME=crs12  SIZE=10 value="360"></TD>
<TD></TD>
<TD><INPUT TYPE=TEXT NAME=d12  SIZE=10 value="0.0"></TD>
</TR>
<CAPTION> Input data
</TABLE>
</FORM>
<P></P>
<P></P>

<FORM NAME="OutputFormDir" method=POST>
<TABLE border=1>
<TR>
<TD COLSPAN=2><DIV ALIGN=CENTER>Lat2</DIV></TD>

<TD COLSPAN=2><DIV ALIGN=CENTER>Lon2</DIV></TD>

</TR>
<TR>
<TD><INPUT TYPE=TEXT NAME=lat2    SIZE=11 ></TD>
<TD><INPUT TYPE=TEXT NAME=lat2ns  SIZE=1 ></TD>
<TD><INPUT TYPE=TEXT NAME=lon2    SIZE=11 ></TD>
<TD><INPUT TYPE=TEXT NAME=lon2ew  SIZE=1 ></TD>
</TR>
<CAPTION> Output
</TABLE>
</CENTER>

<P> Distance Units: 
<SELECT Name="Dunit">
   <OPTION SELECTED>nm
   <OPTION>km
   <OPTION>sm
   <OPTION>ft
</SELECT>
    Earth model:
<SELECT Name="Model">
   <OPTION>Spherical (1'=1nm)
   <OPTION SELECTED>WGS84/NAD83/GRS80
   <OPTION>Clarke (1866)/NAD27
   <OPTION>International
   <OPTION>Krasovsky
   <OPTION>Bessel (1841)
   <OPTION>WGS72
   <OPTION>WGS66
   <OPTION>FAI sphere
   <OPTION>User defined
</SELECT>
</P>

<P>
<INPUT TYPE="button" VALUE="Compute" onClick="ComputeFormDir()">
<INPUT TYPE="button"  VALUE="Reset" onClick="ClearFormDir()">
</P>

</FORM>
<HR>
<H3> Spheroid </H3>
<P> Enter "user defined" spheroid parameters here: </P>
<FORM NAME="spheroid" method="POST">
<P>
 Major radius a (km):
<INPUT TYPE=TEXT NAME=major_radius  SIZE=10 >
 Inverse flattening 1/f:
<INPUT TYPE=TEXT NAME=inverse_f  SIZE=10 >
</P>
<HR>
<P>
Get lat/lon information on:
<SELECT NAME="Fixtype">
 <OPTION SELECTED>Airport<OPTION>Navaid<OPTION>Intersection</SELECT>

<INPUT TYPE=TEXT Name="Fix" SIZE=5 onChange="Link()">
from <A HREF=http://www.airnav.com> Paulo Santos' Airnav </A> site.
</P>
<HR>
<UL>
   <LI><A HREF=index.htm>Home page</A></LI>
   <LI><A HREF=avform.htm>Aviation formulary</A></LI>
   <LI><A HREF="http://www.netonecom.net/~rburtch/geodesy/datums.html"> Coordinates, Datums and Transformations</A></LI>
   <LI><A HREF="http://www.lsgi.polyu.edu.hk/cyber-class/geodesy/index.htm"> Geodesy cyber-class</A></LI>
   <LI><A HREF="http://www.gpsy.com/gpsinfo/"> GPS resource library</A></LI>
   <LI><A HREF="http://www.auslig.gov.au/geodesy/datums/calcs.htm"> Geodetic calculations from Australian Geodetic survey</A></LI>
   <LI><A HREF="ftp://ftp.ngs.noaa.gov/pub/pcsoft/for_inv.3d/source/"> Fortran source for the Vicenty ellipsoidal algorithm</A></LI>
   <LI><A HREF="http://www.utexas.edu/depts/grg/gcraft/notes/datum/gif/refellip.gif"> Reference ellipsoid parameters</A></LI>
   <LI><A HREF="http://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf"> Vincenty's paper in Survey Review.</A></LI>
   <LI><A HREF="http://williams.best.vwh.net/ellipsoid/ellipsoid.html"> The beginnings of a review paper on navigation on a spheroidal earth</A></LI>
</UL>
<P></P>
</FORM>
<H3> History </H3>
<p> 6/8/03  Added option to get distance in feet </p>
<p> 11/4/02 Added references.</p>
<p> 8/20/01 Added FAI sphere. Made statute mile conversion to 10 sig figs
instead of 6.
</p>
<p>
3/23/00 Added warning notes about not starting at poles.
Changed default ellipsoid to WGS84
</p>
<P>
7/13/98 Removed a line of debugging code, giving irritating Javascript alerts, left
over from the 5/16/98 changes
</P>
<P>
5/16/98
Changed the great circle radial and distance algorithm to one valid for
unlimited distances. Previous was only valid for ranges up to one quarter of
the earth's circumference in longitude.
 Note that the Vicenty algorithm for (ellipsoidal) course and distance may
fail to converge correctly, or at all, if the final point is within 37'
of arc of the antipodes of the first point.
</P>
<P>
5/12/98 Eccentricity of NAD27 (Clarke1866) ellipsoid obtained from my reference
"Coordinate Systems and Map Projections" by D. H. Maling was in error.
1/f changed from 298.97866982 to 294.9786982138
</P><P>

11/9/97 Fixed bug where if the output lat/lon was  DD 6.MMMM (ie 6 minutes),
the result was incorrectly rounded up to the next degree.
</P>
3/4/97 Fixed bug where deg/minute entries 08 or 09 would be (mis)read in octal!
</P><P>
<DD>Ed Williams<BR><A HREF="mailto:72347.1516@CompuServe.COM">72347.1516@CompuServe.COM</A></DD>
</BODY>
</HTML>
