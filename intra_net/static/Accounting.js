<div id="purchaser-clearing-utility"></div>
<script>
    Dropzone.autoDiscover = false;

    const state = initialState();

    const view = state => {
        // !! The string has to start with an element as the very first
        // !! character, or AppRun will fail to render with no error.
        const html = `<div id="app-run-container">
            ${errorMessage(state)}

            <div id="flex-container">

                <div id="flex-left-panel">
                <div id="buttons">
                    <button id="run-button" class="button" onclick="app.run('Compare'); app.run('ReviewMonth');" ${runButtonState(state)}>${runButtonText(state)}</button>
                    <button id="asset-listing-button" class="button" onclick="app.run('AssetListing')" ${assetListingButtonState(state)}>${assetListingButtonText(state)}</button>
                    <button id="linking-template-button" class="button" onclick="app.run('BrowseLinkingTemplate')" ${linkingTemplateButtonState(state)}>${linkingTemplateButtonText(state)}</button>
                    <input type="file" name="linking_file" id="linking-file" onchange="app.run('LinkingTemplate')">
					<button id="reset-button" class="button" onclick="app.run('Reset')">Reset</button>
                </div>
                <div id="controls">
                    <div id="company-list" class="control">
                    {% for company in companies %}
                        <div id="company-box-{{ company | replace(' ' , '-')}}" class="company-box dropzone ${companySelected(state, '{{company}}')}">
                            <div id="company-box-msg-{{ company | replace(' ', '-') }}" class="dz-message" data-dz-message>
                                {{ company }}
                            </div>
                        </div>
                    {% endfor %}
                    </div>

                    <div id="month-picker" class="flex-control">
                        <table id="month-picker-table">
                            <tr class="month-picker-row year-selector">
                                <td class="month-picker-cell year-cell year-dec" onclick="app.run('DecrementYear')">&#8592;</td>
                                <td class="month-picker-cell year-cell year" data-ctrl="year-label">${state.selected_year}</td>
                                <td class="month-picker-cell year-cell year-inc" onclick="app.run('IncrementYear')">&#8594;</td>
                            </tr>
                            <tr class="month-picker-row">
                                <td class="month-picker-cell ${monthSelected(state, "01")}" onclick="app.run('ToggleMonth', '01')">Jan</td>
                                <td class="month-picker-cell ${monthSelected(state, "02")}" onclick="app.run('ToggleMonth', '02')">Feb</td>
                                <td class="month-picker-cell ${monthSelected(state, "03")}" onclick="app.run('ToggleMonth', '03')">Mar</td>
                            </tr>
                            <tr class="month-picker-row">
                                <td class="month-picker-cell ${monthSelected(state, "04")}" onclick="app.run('ToggleMonth', '04')">Apr</td>
                                <td class="month-picker-cell ${monthSelected(state, "05")}" onclick="app.run('ToggleMonth', '05')">May</td>
                                <td class="month-picker-cell ${monthSelected(state, "06")}" onclick="app.run('ToggleMonth', '06')">Jun</td>
                            </tr>
                            <tr class="month-picker-row">
                                <td class="month-picker-cell ${monthSelected(state, "07")}" onclick="app.run('ToggleMonth', '07')">Jul</td>
                                <td class="month-picker-cell ${monthSelected(state, "08")}" onclick="app.run('ToggleMonth', '08')">Aug</td>
                                <td class="month-picker-cell ${monthSelected(state, "09")}" onclick="app.run('ToggleMonth', '09')">Sep</td>
                            </tr>
                            <tr class="month-picker-row">
                                <td class="month-picker-cell ${monthSelected(state, "10")}" onclick="app.run('ToggleMonth', '10')">Oct</td>
                                <td class="month-picker-cell ${monthSelected(state, "11")}" onclick="app.run('ToggleMonth', '11')">Nov</td>
                                <td class="month-picker-cell ${monthSelected(state, "12")}" onclick="app.run('ToggleMonth', '12')">Dec</td>
                            </tr>
                        </table>
                    </div>

                <!-- end controls -->
                </div>
                <!-- end flex-left-panel -->
                </div>
                <div id="flex-right-panel">
                ${showReview(state)}
                </div>
            </div>
            </div>
            <div id="unicorn">
                <div class="rainbow">Success</div>
            </div>`;

        return html;
    };

    function showReview(state) {
        if (state.review) {
            var matched = 'calculated-unmatched';
            if (state.review.check_amount_matched) {
                matched = 'calculated-matched';
            }
            return `
                    <table id="review-table">
                        <tr class="review-header">
                            <td class="review-label">Purchaser Clearing</td>
                            <td class="review-value">${state.review.purchaser_clearing_total}</td>
                        </tr>
                        <tr class="review-header">
                            <td class="review-label">Journal Entry Total</td>
                            <td class="review-value">${state.review.total_journal_entry}</td>
                        </tr>
                        <tr class="review-header">
                            <td class="review-label">Check Amount Total</td>
                            <td class="review-value ${matched}">${state.review.total_check_amount}</td>
                        </tr>
                        <tr class="review-header">
                            <td class="review-label normal-header">Owner Net Total</td>
                            <td class="review-value">${state.review.total_onet_amount}</td>
                        </tr>
                        <tr class="review-header">
                            <td class="review-label normal-header">Max Rounding Error</td>
                            <td class="review-value">${state.review.max_rounding_error}</td>
                        </tr>
                        ${showRevenueAccounts(state.review.revenue_accounts, state.review.misc_over_5)}
                        ${showExpenseAccounts(state.review.expense_accounts)}
                    </table>

                    <button id="finalize-button" class="button" onclick="app.run('FinalizeMonth')" ${finalizeButtonState(state)}>${finalizeButtonText(state)}</button>
                    `;
        } else {
            return "";
        }
    }

    function showRevenueAccounts(revenue_accounts, misc_over_5) {
        account_rows = '';
        Object.keys(revenue_accounts).forEach(key => {
            if (key == 'Revenue Total') {
                account_rows = account_rows + `
                        <tr class="review-detail">
                            <td class='total-line'></td>
                            <td class='total-line'>${revenue_accounts[key]}</td>
                        </tr>`;
            } else {
                if ((key == 'Miscellaneous Royalty Income') && misc_over_5) {
                    klass = 'red';
                } else {
                    klass = '';
                }
                account_rows = account_rows + `
                        <tr class="review-detail">
                            <td class='review-label'>${key}</td>
                            <td class='review-value ${klass}'>${revenue_accounts[key]}</td>
                        </tr>`;
            }

        });
        accounts = `
                <tr class="review-header">
                    <td style="padding-bottom: 10px">Revenue Accounts</td>
                    <td style="padding-buttom: 10px"></td>
                </tr>
                ${account_rows}`;

        return accounts;
    }

    function showExpenseAccounts(expense_accounts) {
        account_rows = '';
        Object.keys(expense_accounts).forEach(key => {
            if (key == 'Expense Total') {
                account_rows = account_rows + `
                        <tr class="review-detail">
                            <td class='total-line'></td>
                            <td class='total-line'>${expense_accounts[key]}</td>
                        </tr>`;
            } else {
                account_rows = account_rows + `
                        <tr class="review-detail">
                            <td>${key}</td>
                            <td>${expense_accounts[key]}</td>
                        </tr>`;
            }
        });
        accounts = `
                <tr class="review-header">
                    <td>Expense Accounts</td>
                    <td></td>
                </tr>
                ${account_rows}`;

        return accounts;
    }

    const update = {
        'DecrementYear': state => shiftYear(state, -1),
        'IncrementYear': state => shiftYear(state, 1),
        'ToggleMonth': (state, el, ordinal) => toggleMonth(state, el, ordinal),
        'UploadSucceeded': (state, entity, file) => uploadSucceeded(state, entity, file),
        'UploadFailed': (state, entity, file, error) => uploadFailed(state, entity, file, error),
        'Compare': state => comparePurchaserClearing(state),
        'Reset': state => initialState(),
        'DownloadSucceeded': state => downloadSucceeded(state),
        'DownloadFailed': (state, error) => downloadFailed(state, error),
        'ReviewMonth': state => reviewMonth(state),
        'ReviewSucceeded': (state, data) => reviewSucceeded(state, data),
        'ReviewFailed': (state, error) => reviewFailed(state, error),
        'FinalizeMonth': (state) => finalizeMonth(state),
        'FinalizeSucceeded': (state, data) => finalizeSucceeded(state, data),
        'FinalizeFailed': (state, error) => finalizeFailed(state, error),
        'AssetListing': state => createAssetListing(state),
        'AssetListingSucceeded': (state, data) => assetListingSucceeded(state, data),
        'AssetListingFailed': (state, error) => assetListingFailed(state, error),
        'BrowseLinkingTemplate': state => browseLinkingTemplate(state),
        'LinkingTemplate': state => linkProperties(state),
        'LinkingSucceeded': (state, data) => linkingSucceeded(state, data),
        'LinkingErrorFile': (state, file_data) => linkingErrorFile(state, file_data),
        'LinkingFailed': (state, error, data) => linkingFailed(state, error, data)
    };

    /*************************/
    /*** Utility Functions ***/
    /*************************/
    function someSelection(state) {
        if ((Object.keys(state.cdex_files).length > 0) &&
            state.selected_months.length > 0) {
            return true;
        } else {
            return false
        }
    }

    function oneSelection(state) {
        if ((Object.keys(state.cdex_files).length == 1) && state.selected_months.length == 1) {
            return true;
        } else {
            return false;
        }
    }

    function atLeastOneSelection(state) {
        if (Object.keys(state.cdex_files).length >= 1) {
            return true;
        } else {
            return false;
        }
    }

    function oneCompany(state) {
        if (Object.keys(state.cdex_files).length == 1) {
            return true;
        } else {
            return false;
        }
    }

    function active(state) {
        if (state.comparing || state.reviewing || state.finalizing || state.creating_listing || state.linking) {
            return true;
        } else {
            return false;
        }
    }

    function errorMessage(state) {
        var div_error_message = '';
        if (state.error_message) {
            let msg = escape(state.error_message).replace('\n', '<br>');
            div_error_message = `<div id="error-message">${msg}</div>`;
        }
        return div_error_message;
    }

    function runButtonState(state) {
        if (someSelection(state) && !active(state)) {
            return '';
        } else {
            return 'disabled';
        }
    }

    function runButtonText(state) {
        if (state.comparing) {
            return 'Comparing...';
        } else {
            return 'Run Purchaser Clearing';
        }
    }

    function reviewButtonText(state) {
        if (state.reviewing) {
            return 'Reviewing...';
        } else {
            return 'Review Allocations';
        }
    }

    function reviewButtonState(state) {
        if (oneSelection(state) && !active(state)) {
            return '';
        } else {
            return 'disabled';
        }
    }

    function assetListingButtonState(state) {
        if (atLeastOneSelection(state) && !active(state)) {
            return '';
        } else {
            return 'disabled';
        }
    }

    function assetListingButtonText(state) {
        if (state.creating_listing) {
            return 'Creating...';
        } else {
            return 'Create Asset Listing';
        }
    }

    function linkingTemplateButtonState(state) {
        if (!active(state)) {
            return '';
        } else {
            return 'disabled';
        }
    }

    function linkingTemplateButtonText(state) {
        if (state.linking) {
            return 'Linking...';
        } else {
            return 'Upload Linking Template';
        }
    }

    function companySelected(state, entity) {
        if (entity in state.cdex_files) {
            return 'selected';
        } else {
            return 'unselected';
        }
    }

    function monthSelected(state, ord) {
        const year_month = state.selected_year + '-' + ord;
        var selection_class = 'unselected';
        if (state.selected_months.includes(year_month)) {
            selection_class = 'selected';
        }
        return selection_class;
    }

    function currentYear() {
        var d = new Date();
        return d.getFullYear();
    }

    function escape(text) {
        var rAmp = /&/g;
        var rLt = /</g;
        var rApos = /\'/g;
        var rQuot = /\"/g;
        var hChars = /[&<>\"\']/;

        if (text == null) {
            return text;
        }

        if (typeof text !== "string") {
            text = String(text);
        }

        if (hChars.test(String(text))) {
            return text
                .replace(rAmp, '&amp;')
                .replace(rLt, '&lt;')
                .replace(rApos, '&apos;')
                .replace(rQuot, '&quot;');
        } else {
            return text;
        }
    }

    function saveAsExcel(data, filename) {
        var blob = toBlob(data);
        var link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = filename;
        link.click();
    }

    function toBlob(base64) {
        var byteCharacters = atob(base64);
        var byteNumbers = new Array(byteCharacters.length);
        for (var i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        var byteArray = new Uint8Array(byteNumbers);

        // now that we have the byte array, construct the blob from it
        var blob = new Blob([byteArray], {
            type: "application/octet-stream"
        });
        return blob;
    }

    function today() {
        const d = new Date();
        return d.toISOString().slice(0, 10)
    }
    /*************************/
    /* End Utility Functions */
    /*************************/


    /**********************/
    /** Update Functions **/
    /**********************/
    function initialState() {
        $('#unicorn').css({
            opacity: '',
            top: ''
        });
        return {
            cdex_files: {},
            selected_months: [],
            error_message: null,
            selected_year: currentYear(),
            comparing: false,
            reviewing: false,
            finalizing: false,
            creating_listing: false,
            linking: false,
            finalize_succeeded: null,
            review: null
        }
    }

    function shiftYear(state, shift) {
        state.selected_year = state.selected_year + shift;
        return state;
    }

    function toggleMonth(state, month_ord) {
        const year_month = state.selected_year + '-' + month_ord;
        if (state.selected_months.includes(year_month)) {
            state.selected_months = state.selected_months.filter(x => x != year_month);
        } else {
            state.selected_months.push(year_month);
        }
        return state;
    }

    function uploadSucceeded(state, entity, file) {
        state.cdex_files[entity] = file;
        return state;
    }

    function uploadFailed(state, entity, file, error) {
        const line_1 = `Failed to upload file < ${file.name}> for <${entity}>.`;
        state.error_message = `${line_1}<Error: ${error}>`;
        return state;
    }

    function comparePurchaserClearing(state) {
        const entities = Object.keys(state.cdex_files).join(',');
        const entities_hyphenated = Object.keys(state.cdex_files).join('-');
        const txn_months = state.selected_months.join(',');
        const params = `entities=${entities}&txn_months=${txn_months}`;
        $.get(`/accounting/purchaser-clearing/comparison?${params}`, function(result) {
            if (result.type == 'file') {
                filename = `purchaser_clearing_${entities_hyphenated}_${today()}.xlsx`;
                saveAsExcel(result.data, filename);
                app.run('DownloadSucceeded');
            } else {
                app.run('DownloadFailed', result.message);
            }
        }).fail(function(jqXHR, textStatus, errorThrown) {
            app.run('DownloadFailed', errorThrown);
        });

        state.comparing = true;
        return state;
    }

    function downloadSucceeded(state) {
        state.comparing = false;
        return state;
    }

    function downloadFailed(state, error) {
        state.error_message = `Download failed: <${error}>`;
        state.comparing = false;
        return state;
    }

    function reviewMonth(state) {
        if (!oneSelection(state)) {
            app.run('ReviewFailed', "Select a single company and month to review.");
            return state;
        }
        const entity = Object.keys(state.cdex_files)[0];
        const gl_month = state.selected_months[0];
        const params = `entity=${entity}&gl_month=${gl_month}`;
        $.get(`/accounting/purchaser-clearing/review?${params}`, function(result) {
            if (result.type == 'json') {
                app.run('ReviewSucceeded', result.data);
            } else {
                app.run('ReviewFailed', result.message);
            }
        }).fail(function(jqXHR, textStatus, errorThrown) {
            app.run('ReviewFailed', errorThrown);
        });

        state.reviewing = true;
        return state;
    }

    function reviewSucceeded(state, data) {
        state.reviewing = false;
        state.review = data;
        return state;
    }

    function reviewFailed(state, error) {
        state.error_message = error;
        state.reviewing = false;
        return state;
    }

    function finalizeButtonState(state) {
        if (state.finalize_succeeded == false) {
            // Already finalized and it failed.
            return 'disabled';
        } else if (state.finalize_succeeded == true) {
            // Already finalized, so don't allow another for this same
            // month and entity.
            return 'disabled';
        } else if (state.review.check_amount_matched == true) {
            // The MineralSoft check amount total matches QBO,
            // so allow finalization.
            return '';
        } else {
            return 'disabled';
        }
    }

    function finalizeButtonText(state) {
        if (state.finalizing) {
            return 'Finalizing...';
        } else if (state.finalize_succeeded == false) {
            return 'Finalization Failed';
        } else if (state.finalize_succeeded == true) {
            return 'Finalization Complete';
        } else {
            return 'Finalize Month';
        }
    }

    function finalizeMonth(state) {
        let review_id = state.review.id;
        $.get(`/accounting/purchaser-clearing/finalize?id=${review_id}`, function(result) {
            if (result.type == 'json') {
                app.run('FinalizeSucceeded', result.data);
            } else {
                app.run('FinalizeFailed', result.message);
                if (result.data) {
                    console.log(`Error details below:`);
                    console.log(result.data);
                }
            }
        }).fail(function(jqXHR, textStatus, errorThrown) {
            app.run('FinalizeFailed', errorThrown);
        });

        state.finalizing = true;
        return state;
    }

    function finalizeSucceeded(state, data) {
        state.finalizing = false;
        state.finalize_succeeded = true;
        $('#unicorn').animate({
            opacity: 1.0,
            top: 100,
        }, 1000);
        return state;
    }

    function finalizeFailed(state, error) {
        state.error_message = error;
        state.finalizing = false;
        state.finalize_succeeded = false;
        return state;
    }

    function createAssetListing(state) {
        let entities = Object.keys(state.cdex_files).join(',');
        $.get(`/accounting/purchaser-clearing/create-asset-listing?entities=${entities}`, function(result) {
            if (result.type == 'file') {
                let entities_hyphenated = Object.keys(state.cdex_files).join('-');
                filename = `asset_listing_${entities_hyphenated}_${today()}.xlsx`;
                saveAsExcel(result.data, filename);
                app.run('AssetListingSucceeded', result.data);
            } else {
                app.run('AssetListingFailed', result.message);
            }
        }).fail(function(jqXHR, textStatus, errorThrown) {
            app.run('AssetListingFailed', errorThrown);
        });

        state.creating_listing = true;
        return state;
    }

    function assetListingSucceeded(state, data) {
        state.creating_listing = false;
        return state;
    }

    function assetListingFailed(state, error) {
        state.error_message = `Asset Listing Failed: ${error}`;
        state.creating_listing = false;
        return state;
    }

    function browseLinkingTemplate(state) {
        $('#linking-file').click();
    }

    function linkProperties(state) {
        var fd = new FormData();
        var file = $('#linking-file')[0].files[0];
        fd.append('file', file);
        $.ajax({
            url: 'linking-template',
            type: 'post',
            data: fd,
            contentType: false,
            processData: false,
            success: function(result) {
                if (result.type == 'json') {
                    app.run('LinkingSucceeded', result.data);
                } else if (result.type == 'file') {
                    app.run('LinkingErrorFile', result.data);
                } else {
                    app.run('LinkingFailed', result.message, result.data);
                }
            },
        });

        state.linking = true;
        return state;
    }

    function linkingSucceeded(state, data) {
        console.log(data);
        state.linking = false;
        return state;
    }

    function linkingErrorFile(state, file_data) {
        state.linking = false;
        state.error_message = 'Linking Failed. Review the issues in the downloaded Excel file under the <error> column.';
        saveAsExcel(file_data, 'linking_errors.xlsx');
        return state;
    }

    function linkingFailed(state, error, data) {
        console.log(data);
        state.error_message = `Linking Failed: ${error}`;
        state.linking = false;
        return state;
    }
    /**************************/
    /** End Update Functions **/
    /**************************/

    /****** Start AppRun ******/
    app.start('purchaser-clearing-utility', state, view, update);
    /**** End Start AppRun ****/

    /**************************/
    /* Dropzone Configuration */
    /**************************/
    $(document).ready(function() {
        /* Prevent drag and select when clicking buttons. */
        $('.month-picker-cell').mousemove(function(e) {
            // prevent drag and select.
            e.preventDefault();
        });
        $('.company-box').mousemove(function(e) {
            // prevent drag and select
            e.preventDefault();
        });

        function createDropzone(dropzone_id, dropzone_msg_id) {
            var entity = $(dropzone_id).text().trim();
            var dropzone = new Dropzone(dropzone_id, {
                paramName: "file", // The name that will be used to transfer the file
                maxFilesize: 200, // MB
                timeout: 600000, // milliseconds
                accept: function(file, done) {
                    if (file.name.endsWith('csv')) {
                        done();
                    } else {
                        done('Check Stub Data Dump should be a CSV file.');
                    }
                },
                url: '/accounting/purchaser-clearing/file-upload?entity=' + entity,
                dragover: function(event) {
                    var el = document.querySelector(dropzone_id);
                    el.style.backgroundColor = 'aliceblue';
                },
                dragleave: function(event) {
                    var el = document.querySelector(dropzone_id);
                    el.style.backgroundColor = 'white';
                },
                success: function(file, response) {
                    var el = document.querySelector(dropzone_id);
                    el.className += " upload-complete";
                    app.run("UploadSucceeded", entity, file);
                },
                error: function(file, errorMessage) {
                    app.run("UploadFailed", entity, file, errorMessage);
                }
            });

            return dropzone;
        }

        { %
            for company in companies %
        }
        createDropzone("#company-box-{{ company | replace(' ', '-') }}", "#dropzone-msg"); { % endfor %
        }
    });
</script>