function submit_prompt() {
    
    const textPrompt = document.getElementById('text-prompt').value;
    const personaId = document.getElementById('persona-id').value;

    const payload = {
        'text_prompt': textPrompt,
        'persona_id': personaId
    };

    fetch('/submit_prompt', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      })
        .then(
            (response) => response.json()
        )
        .then((jsonResponse) => {
          console.log('Fetch success:', jsonResponse);
          
          if (jsonResponse.Status == "OK") {
            const audioUrl = jsonResponse.audio_check_url;
            // Show loading gif
            document.getElementById('loading').style.display = 'block';
            // Wait for the audio file to be ready and play it
            pollAudioUrlAndPlay(audioUrl);
          }
          else {
            console.error('Error submitting the text prompt');
          }
    
        });
};

async function pollAudioUrlAndPlay(audioUrl) {
    const audioPlayer = document.getElementById('audio-player');
    try {
        const response = await fetch(`/fetch_audio?url=${encodeURIComponent(audioUrl)}`);
        if (response.ok) {
            // Hide loading gif
            document.getElementById('loading').style.display = 'none';
            // Update the audio player source and display it
            audioPlayer.src = `/fetch_audio?url=${encodeURIComponent(audioUrl)}`;
            audioPlayer.style.display = 'block';
            // Play the audio
            audioPlayer.play();
        } else {
            setTimeout(() => pollAudioUrlAndPlay(audioUrl), 1000);
        }
    } catch (error) {
        console.error('Error fetching the audio URL:', error);
    }
}

function update_photo() {
  const selected_persona = document.getElementById('persona-id').value;
  const photo_element = document.getElementById('person-photo');
  photo_element.src = `https://chatgptstorage57382.blob.core.windows.net/static/${selected_persona}.png`;

  // Hide the audio player after switching personas
  document.getElementById('audio-player').style.display = 'none';
}