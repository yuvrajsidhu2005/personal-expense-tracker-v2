document.addEventListener("DOMContentLoaded", function () {
    // === REMOVED: No more addMotion, no scaling, no zoom on card/widget hover or focus ===

    // Chart.js: animate on pie/bar segment hover (optional visual, not related to cards)
    if (window.Chart) {
        Chart.defaults.plugins.legend.labels.generateLabels = function(chart) {
            return Chart.defaults.plugins.legend.labels.generateLabels.apply(this, arguments)
                .map(label => {
                    label.pointStyle = 'circle';
                    return label;
                });
        };
    }

    // Description autocomplete (as before)
    const descInput = document.getElementById('description');
    const suggestionBox = document.getElementById('desc-suggestions');
    if(descInput && suggestionBox) {
        let lastQuery = "";
        descInput.addEventListener('input', function() {
            const q = this.value.trim();
            if(q.length < 1) { suggestionBox.style.display = 'none'; return; }
            lastQuery = q;
            fetch(`/suggest_descriptions?q=${encodeURIComponent(q)}`)
              .then(res => res.json())
              .then(data => {
                if(descInput.value.trim() !== lastQuery) return;
                suggestionBox.innerHTML = "";
                if(data.length) {
                  data.forEach(s => {
                    let el = document.createElement('button');
                    el.type = 'button';
                    el.className = 'list-group-item list-group-item-action';
                    el.textContent = s;
                    el.onclick = () => { descInput.value = s; suggestionBox.style.display = 'none'; };
                    suggestionBox.appendChild(el);
                  });
                  suggestionBox.style.display = 'block';
                } else { suggestionBox.style.display = 'none'; }
              });
        });
        document.addEventListener('click', function(e){
            if(!suggestionBox.contains(e.target) && e.target !== descInput) {
                suggestionBox.style.display = 'none';
            }
        });
    }

    // Dynamic add tag chips for tag fields (if present)
    document.querySelectorAll(".tag-input").forEach(tagInput => {
        tagInput.addEventListener("keydown", function(e) {
            if (e.key === "," || e.key === "Enter") {
                e.preventDefault();
                let val = tagInput.value.trim().replaceAll(",", "");
                if(val) {
                    let chip = document.createElement("span");
                    chip.className = "badge rounded-pill bg-primary mx-1 mb-1 tagchip";
                    chip.textContent = val;
                    chip.onclick = () => chip.remove();
                    tagInput.parentElement.insertBefore(chip, tagInput);
                    tagInput.value = "";
                }
            }
        });
        // Collect all tag values into hidden field on submit
        tagInput.form && tagInput.form.addEventListener("submit", function(e){
            let tags = Array.from(tagInput.parentElement.querySelectorAll('.tagchip')).map(t => t.textContent);
            tagInput.value = tags.join(",");
        });
    });

    // Dynamic theme switching
    document.querySelectorAll(".theme-switch").forEach(btn => {
        btn.onclick = function() {
            let theme = this.getAttribute("data-theme");
            fetch(`/set_theme?theme=${encodeURIComponent(theme)}`).then(()=>location.reload());
        };
    });

    // Onboarding/help modal (if present)
    let onboarding = document.getElementById("onboardingModal");
    if(onboarding) {
        new bootstrap.Modal(onboarding).show();
    }

    // Budget input slider helper (if present)
    document.querySelectorAll(".budget-slider-group").forEach(group => {
        const slider = group.querySelector("input[type=range]");
        const label = group.querySelector(".budget-amount");
        if(slider && label) {
            slider.oninput = function() { label.textContent = "₹" + slider.value; }
            slider.oninput();
        }
    });
});
