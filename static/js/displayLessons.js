function displayLessons(data){
    var lesson_data = '';
    $.each(data,function(key,value){
                       
        for (i=0; i < value.length; i++){

            lesson_data += '<tr>';
            lesson_data += '<td>'+value[i].lessonName+'</td>';
            lesson_data += '<td>'+'<input type="number" name="'+value[i].id+'" max="30" class="form-control" placeholder="Last name" value="'+value[i].lessonOrder+'">'+'</td>';
                        
            lesson_data += '</tr>';
        }  
                    
    });
                    
    $('#lesson-tbody').html(lesson_data);
}