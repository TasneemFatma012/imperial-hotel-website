function ch1(){
    a=document.getElementById("i6").value
    document.getElementById("A").innerHTML=a
    b=document.getElementById("i7").value
    document.getElementById("B").innerHTML=b
    c=document.getElementById("i8").value
    document.getElementById("C").innerHTML=c
    d=document.getElementById("i9").value
    document.getElementById("D").innerHTML=d
    e=document.getElementById("i10").value
    document.getElementById("E").innerHTML=e
   

}

    function ch(){
        a=document.getElementById("u1").value
    document.getElementById("m1").innerHTML=a
    b=document.getElementById("u2").value
    document.getElementById("m2").innerHTML=b
    c=document.getElementById("u3").value
    document.getElementById("m3").innerHTML=c
    d=document.getElementById("u4").value
    document.getElementById("m4").innerHTML=d
    e=document.getElementById("u5").value
    document.getElementById("m5").innerHTML=e
    f=document.getElementById("u6").value
    document.getElementById("m6").innerHTML=f
    g=document.getElementById("u7").value
    document.getElementById("m7").innerHTML=g
    h=document.getElementById("u8").value
    document.getElementById("m8").innerHTML=h

    
    k=document.getElementById("type").value
    document.getElementById("m10").innerHTML=k
    
    l=document.getElementById("u11").value
    document.getElementById("m11").innerHTML=l
    
    if(k=="singleroom"){
        tp =(h+l)*500   
        document.getElementById("m12").innerHTML=tp
    }
    }