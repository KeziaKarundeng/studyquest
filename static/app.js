// Navigation uses normal links so every page initializes reliably and supports back/forward.
const $ = selector => document.querySelector(selector);
function closeXPModal(){ $('#xp-modal').classList.remove('active'); }
function closeLevelUpModal(){ $('#levelup-modal').classList.remove('active'); }
function closeBadgeModal(){ $('#badge-modal').classList.remove('active'); }
function showXPModal(amount,reason){$('#xp-amount').textContent=`+${amount} XP`;$('#xp-reason').textContent=reason;$('#xp-modal').classList.add('active');}
async function api(url,options={}){
    const response=await fetch(url,options);
    const data=await response.json();
    if(!response.ok || data.status==='error') throw new Error(data.pesan || 'Belum berhasil. Coba lagi, yuk.');
    return data;
}
function feedback(message,error=false){
    let el=$('#action-feedback');
    if(!el){el=document.createElement('div');el.id='action-feedback';el.setAttribute('role','status');$('.main-content').prepend(el);}
    el.className='form-feedback'+(error?' error':'');el.textContent=message;
}
document.addEventListener('click',async event=>{
    const filter=event.target.closest('[data-mission-filter]');
    if(filter){
        document.querySelectorAll('[data-mission-filter]').forEach(button=>{const active=button===filter;button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});
        let visible=0;document.querySelectorAll('.mission-item[data-jenis]').forEach(card=>{card.hidden=filter.dataset.missionFilter!=='semua' && card.dataset.jenis!==filter.dataset.missionFilter;if(!card.hidden) visible++;});
        $('#filter-empty').hidden=visible>0;return;
    }
    const complete=event.target.closest('[data-complete-id]');
    const remove=event.target.closest('[data-delete-id]');
    const edit=event.target.closest('[data-edit-id]');
    if(edit){window.location.href='/missions?edit='+encodeURIComponent(edit.dataset.editId);return;}
    if(!complete && !remove)return;
    if(remove && !confirm('Hapus misi ini?'))return;
    if(complete && !confirm('Misi ini sudah beres? Tandai selesai dan ambil XP-mu.'))return;
    const button=complete || remove;button.disabled=true;
    try{
        const id=complete?complete.dataset.completeId:remove.dataset.deleteId;
        const result=await api('/api/missions/'+encodeURIComponent(id)+(complete?'/complete':''),{method:complete?'POST':'DELETE'});
        if(complete){
            showXPModal(result.data.xp_diberikan,result.data.pesan);
            const close=()=>window.location.reload();
            $('#xp-modal').addEventListener('click',close,{once:true});
            document.addEventListener('keydown',e=>{if(e.key==='Escape')close();},{once:true});
            setTimeout(close,1800);
        }else window.location.reload();
    }catch(error){feedback(error.message,true);button.disabled=false;}
});
document.querySelectorAll('.modal').forEach(modal=>modal.addEventListener('click',event=>{if(event.target===modal)modal.classList.remove('active');}));
document.addEventListener('keydown',event=>{if(event.key==='Escape')document.querySelectorAll('.modal').forEach(modal=>modal.classList.remove('active'));});
// Filter existing rows without injecting user-supplied HTML.
function filterMisi(){
    const jenis=$('#filter-jenis').value,status=$('#filter-status').value,search=$('#search-misi').value.toLocaleLowerCase('id');
    document.querySelectorAll('.mission-row').forEach(row=>{row.hidden=(jenis!=='semua' && row.dataset.jenis!==jenis)||(status!=='semua' && row.dataset.status!==status)||!row.cells[1].textContent.toLocaleLowerCase('id').includes(search);});
    const body=$('#missions-table-body');let empty=$('#search-empty');
    const rows=[...body.querySelectorAll('.mission-row')];
    if(rows.length && rows.every(row=>row.hidden)){
        if(!empty){empty=document.createElement('tr');empty.id='search-empty';const cell=document.createElement('td');cell.colSpan=8;cell.className='empty-state';cell.textContent='Belum ketemu. Coba kata kunci atau filter lain.';empty.append(cell);body.append(empty);}
    }else if(empty)empty.remove();
}
['filter-jenis','filter-status','search-misi'].forEach(id=>{const input=document.getElementById(id);if(input)input.addEventListener('input',filterMisi);});
const missionForm=$('#mission-form');
if(missionForm){
    const editId=new URLSearchParams(window.location.search).get('edit');
    if(editId){
        api('/api/missions').then(data=>{
            const mission=data.misi.find(m=>m.id===editId);if(!mission)throw new Error('Misi tidak ditemukan.');
            $('#misi-id').value=editId;
            for(const [key,value] of Object.entries(mission)){const input=missionForm.elements.namedItem(key==='tenggat'?'tengggat':key);if(input)input.value=value || '';}
            $('.add-mission-form h3').textContent='Edit misi kamu';missionForm.scrollIntoView({block:'start'});
        }).catch(error=>feedback(error.message,true));
    }
    missionForm.addEventListener('submit',async event=>{
        event.preventDefault();const button=missionForm.querySelector('[type=submit]');button.disabled=true;
        const id=$('#misi-id').value;
        try{await api('/api/missions'+(id?'/'+encodeURIComponent(id):''),{method:id?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(missionForm)))});window.location.href='/missions';}
        catch(error){feedback(error.message,true);button.disabled=false;}
    });
}

// Starting a mission records personal progress without awarding completion XP.
document.addEventListener('click', async event => {
    const button = event.target.closest('[data-start-id]');
    if (!button || button.disabled) return;
    button.disabled = true;
    try {
        await api('/api/missions/' + encodeURIComponent(button.dataset.startId) + '/start', {method: 'POST'});
        window.location.reload();
    } catch (error) {
        feedback(error.message, true);
        button.disabled = false;
    }
});

document.addEventListener('submit', async event => {
    const form = event.target.closest('[data-grade-form]');
    if (!form) return;
    event.preventDefault();
    const button = form.querySelector('[type="submit"]');
    if (button.disabled) return;
    const message = form.querySelector('[data-grade-feedback]');
    button.disabled = true;
    message.textContent = 'Menyimpan…';
    try {
        const data = await api('/api/penilaian-pdf', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({id_soal: form.dataset.soal, nim: form.dataset.nim,
                nilai: form.elements.nilai.value, catatan: form.elements.catatan.value})
        });
        form.querySelector('.grade-status').textContent = `Sudah dinilai: ${data.nilai} / 100`;
        message.className = 'grade-feedback';
        message.textContent = data.pesan;
    } catch (error) {
        message.className = 'grade-feedback error';
        message.textContent = error.message;
    } finally {
        button.disabled = false;
    }
});
