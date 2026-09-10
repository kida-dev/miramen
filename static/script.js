navigator.mediaDevices
.getUserMedia({
    video:true,
    audio:false
})
.then(stream=>{

    document.getElementById("camera")
    .srcObject = stream;

})
.catch(error=>{

    alert("カメラが使用できません");

});